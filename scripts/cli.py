"""命令入口：按所选编译环境调用 vcpkg、消费测试和许可收集，并保存日志。"""
import argparse
import configparser
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys

from .config import output_directories, read_config, write_triplet
from .manifest import validate_selection, write_manifest


def run(command, cwd, env, log):
    log.parent.mkdir(parents=True, exist_ok=True)
    print("+ " + subprocess.list2cmdline([str(x) for x in command]), flush=True)
    with log.open("w", encoding="utf-8") as out:
        process = subprocess.Popen([str(x) for x in command], cwd=cwd, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding="utf-8", errors="replace")
        for line in process.stdout:
            out.write(line)
            out.flush()
            print(line, end="", flush=True)
        code = process.wait()
    if code:
        raise RuntimeError(f"Command failed ({code}); log: {log}")


def source_files(root, excluded=()):
    # 默认布局与旧布局统一排除；自定义目录按 config.ini 中的完整路径排除。
    ignored = {".git", "__pycache__", "build", "installed", "install", "downloads", "binary-cache"}
    prefixes = ("build_", "install_", "downloads_", "binary-cache_")
    excluded = {path.resolve() for path in excluded}
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in ignored and not d.startswith(prefixes)
                   and (Path(directory) / d).resolve() not in excluded]
        for name in dirs + files:
            path = Path(directory) / name
            attributes = getattr(path.lstat(), "st_file_attributes", 0)
            if path.is_symlink() or attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
                raise RuntimeError(f"Source contains a link/junction: {path}")
        for name in files:
            path = Path(directory) / name
            local_config = name == "config.ini" or (name.startswith("config.") and name.endswith(".ini"))
            if not local_config and path.resolve() not in excluded:
                yield path


def audit(root, destination, config_file):
    inventory = {}
    violations = []
    for path in source_files(root, [config_file, *output_directories(root, config_file)]):
        rel = path.relative_to(root).as_posix()
        inventory[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        if path.suffix in {".py", ".cmake", ".json", ".txt"} and rel != "scripts/cli.py":
            content = path.read_text(encoding="utf-8")
            if re.search(r"[A-Za-z]:[/\\](?:projectWQZ|app)[/\\]|thirdPartyManager|create_libpack", content):
                violations.append(rel)
        if path.name == "vcpkg.json":
            json.loads(path.read_text(encoding="utf-8"))
    if violations:
        raise RuntimeError("Nonportable source references: " + ", ".join(violations))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(f"Source audit: {len(inventory)} files, no external source paths or links; {destination}")


def verify(root, cfg, args, env, log, installed, jobs):
    """使用同一套 INI 配置构建消费者，再设置对应 SDK 的运行资源路径。"""
    triplets = write_triplet(cfg)
    python_only = args.port == "python3"
    source = root / "tests" / "cpython" if python_only else root / "tests"
    prefix = installed / cfg.triplet
    consumer = cfg.build / ("consumer-python3" if python_only else "consumer")
    if args.installed_root:
        consumer = consumer.with_name(consumer.name + "-" + hashlib.sha256(str(installed).encode()).hexdigest()[:12])
    for config in (["Release", "Debug"] if args.config == "both" else [args.config]):
        build = consumer / config
        generator = ["-G", cfg.generator]
        if cfg.system == "Windows":
            generator += ["-A", "x64", "-T", cfg.toolset,
                          f"-DCMAKE_GENERATOR_INSTANCE={cfg.vs_path}"]
        else:
            generator += [f"-DVCPKG_CHAINLOAD_TOOLCHAIN_FILE={triplets / 'linux-toolchain.cmake'}"]
        run([cfg.cmake, "-S", source, "-B", build, *generator,
             f"-DCMAKE_CXX_STANDARD={cfg.cpp_standard[3:]}",
             f"-DCMAKE_BUILD_TYPE={config}", f"-DCMAKE_TOOLCHAIN_FILE={cfg.vcpkg_root / 'scripts/buildsystems/vcpkg.cmake'}",
             f"-DVCPKG_TARGET_TRIPLET={cfg.triplet}", f"-DVCPKG_HOST_TRIPLET={cfg.triplet}",
             f"-DVCPKG_OVERLAY_TRIPLETS={triplets}",
             f"-DVCPKG_INSTALLED_DIR={installed}", "-DVCPKG_MANIFEST_INSTALL=OFF", "-DVCPKG_APPLOCAL_DEPS=OFF",
             *([f"-DSDK_PYTHON_PREFIX={prefix}"] if python_only else
               [f"-DSDK_FULL={'ON' if args.stage == 'full' else 'OFF'}"])], root, env,
            log.with_stem(log.stem + '-' + config + '-configure'))
        run([cfg.cmake, "--build", build, "--config", config, "--parallel", str(jobs)], root, env,
            log.with_stem(log.stem + '-' + config + '-build'))
        test_env = env.copy()
        bins = [prefix / "debug/bin", prefix / "bin"] if config == "Debug" else [prefix / "bin"]
        test_env["PATH"] = os.pathsep.join(map(str, bins)) + os.pathsep + env.get("PATH", "")
        test_env["QT_QPA_PLATFORM"] = "offscreen"
        test_env["QT_PLUGIN_PATH"] = str(prefix / ("debug/Qt6/plugins" if config == "Debug" else "Qt6/plugins"))
        test_env["SDK_EXPECTED_PREFIX"] = str(prefix)
        test_env["SDK_EXPECTED_CONFIG"] = config
        # Windows Tcl embeds its standard library in zipfs. Do not
        # inherit an unrelated SDK's script directory in either case.
        test_env.pop("TCL_LIBRARY", None)
        test_env.pop("TK_LIBRARY", None)
        if cfg.system == "Windows":
            python_home = prefix / ("tools/python3/debug" if config == "Debug" else "tools/python3")
            test_env["PYTHONHOME"] = str(python_home)
            test_env["PYTHONPATH"] = os.pathsep.join(map(str, [*bins, python_home / "DLLs"]))
            tcl_library = prefix / ("tools/tcl/debug/lib/tcl9.0" if config == "Debug" else "tools/tcl/lib/tcl9.0")
        else:
            config_prefix = prefix / "debug" if config == "Debug" else prefix
            test_env["PYTHONHOME"] = str(config_prefix)
            test_env["PYTHONPATH"] = str(config_prefix / "lib/python3.15t/lib-dynload")
            libdirs = [config_prefix / "lib", prefix / "lib"]
            test_env["LD_LIBRARY_PATH"] = os.pathsep.join([*map(str, libdirs), env.get("LD_LIBRARY_PATH", "")]).rstrip(os.pathsep)
            tcl_library = config_prefix / "lib/tcl9.0"
        if tcl_library.exists():
            test_env["TCL_LIBRARY"] = str(tcl_library)
        tk_library = prefix / ("debug/lib/tk9.0" if config == "Debug" else "lib/tk9.0")
        if tk_library.exists():
            test_env["TK_LIBRARY"] = str(tk_library)
        ctest = cfg.cmake.parent / ("ctest.exe" if cfg.system == "Windows" else "ctest")
        run([ctest, "--test-dir", build, "-C", config, "--output-on-failure", "--no-tests=error"], root, test_env,
            log.with_stem(log.stem + '-' + config + '-test'))


def main(root):
    root = root.resolve()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["paths", "doctor", "audit-source", "plan", "build", "verify", "licenses"])
    parser.add_argument("-c", "--config-file", type=Path, default=root / "config.ini",
                        help="build environment INI; defaults to the repository's config.ini")
    parser.add_argument("-m", "--manifest", type=Path, default=Path("vcpkg.json"),
                        help="dependency JSON file, relative to the repository; defaults to vcpkg.json")
    parser.add_argument("--port", help="select one port while reusing the shared SDK and its installed dependencies")
    parser.add_argument("--rebuild", action="store_true",
                        help="with build --port: rebuild that port and its installed dependents from source")
    parser.add_argument("--installed-root", type=Path,
                        help="verify an existing or relocated SDK; only valid with verify")
    parser.add_argument("--stage", choices=["native", "full"], default="full",
                        help="native is an intermediate phase; full is required for acceptance")
    parser.add_argument("--from-source", action="store_true", help="disable binary cache reads and writes")
    parser.add_argument("--config", choices=["Release", "Debug", "both"], default="both")
    parser.add_argument("--jobs", type=int, help="override JOBS from config.ini")
    parser.add_argument("--clean-buildtrees", action="store_true", help="remove completed buildtrees and staging packages to save disk")
    args = parser.parse_args()
    report = None
    report_data = {}
    try:
        manifest_file = (root / args.manifest).resolve()
        custom_manifest = manifest_file != root / "vcpkg.json"
        if args.rebuild and (args.command != "build" or not args.port):
            raise RuntimeError("--rebuild requires build --port NAME")
        if args.command == "verify" and (custom_manifest or args.port not in (None, "python3")):
            raise RuntimeError("verify supports the default SDK or --port python3; do not select a manifest")
        if args.port and args.stage != "full":
            raise RuntimeError("--port selects one dependency; do not combine it with --stage native")
        if args.installed_root and args.command != "verify":
            raise RuntimeError("--installed-root is only valid with verify")
        system = platform.system()
        if system not in {"Windows", "Linux"}:
            raise RuntimeError("Supported native build hosts: Windows and Linux")
        # 先计算目录；paths 和源码审计不需要编译器或 vcpkg。
        cfg = read_config(root, args.config_file.resolve(), system)
        validate_selection(root, manifest_file, args.port)
        jobs = args.jobs if args.jobs is not None else cfg.jobs
        if jobs < 1:
            raise RuntimeError("--jobs must be positive")
        paths = cfg.paths()
        if args.command == "paths":
            print(json.dumps({"config_file": str(cfg.file), "manifest_file": str(manifest_file),
                              "system": system, "triplet": cfg.triplet,
                              **{key: str(value) for key, value in paths.items()}}, indent=2))
            return 0
        if args.command == "audit-source":
            audit(root, paths["reports"] / "source-inventory.json", cfg.file)
            return 0
        if sys.version_info < (3, 10):
            raise RuntimeError("Host Python 3.10 or newer is required")
        baseline = json.loads((root / "vcpkg-configuration.json").read_text(encoding="utf-8"))["default-registry"]["baseline"]
        external = cfg.vcpkg_root
        exe = external / ("vcpkg.exe" if system == "Windows" else "vcpkg")
        if not exe.is_file():
            raise RuntimeError(f"Missing executable: {exe}")
        triplet = cfg.triplet
        # Same native architecture/compiler: reuse host tools in the same prefix.
        host = triplet
        workspace = cfg.build
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        scope = "python3" if args.command == "verify" and args.port == "python3" else args.stage
        report = workspace / "reports" / f"{args.command}-{scope}.json"
        report_data = {"command": args.command, "stage": args.stage, "success": False,
                       "timestamp": stamp, "system": system, "triplet": triplet,
                       "baseline": baseline, "config_file": str(cfg.file), "manifest_file": str(manifest_file),
                       "port": args.port, "rebuild": args.rebuild,
                       "config": args.config if args.command == "verify" else None,
                       "paths": {key: str(value) for key, value in paths.items()}}
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(report_data, indent=2) + "\n", encoding="utf-8")
        # 只修改当前子进程环境，不改用户的全局环境变量。
        env = os.environ.copy()
        env.update(VCPKG_ROOT=str(external), VCPKG_DOWNLOADS=str(cfg.downloads),
                   VCPKG_DEFAULT_BINARY_CACHE=str(cfg.binary_cache),
                   VCPKG_REGISTRIES_CACHE=str(paths["registries"]),
                   VCPKG_MAX_CONCURRENCY=str(jobs))
        if system == "Windows":
            env["VCPKG_VISUAL_STUDIO_PATH"] = cfg.vs_path
        else:
            env.update(CC=cfg.gcc, CXX=cfg.gxx, AS=cfg.gcc)
            if cfg.library_path:
                env["LD_LIBRARY_PATH"] = cfg.library_path
        report_data["host_triplet"] = host
        for path in [cfg.downloads, cfg.binary_cache, paths["registries"]]:
            path.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "-C", str(external), "cat-file", "-e", baseline + "^{commit}"], check=True,
                       stdout=subprocess.DEVNULL)
        log = workspace / "logs" / f"{stamp}-{args.command}-{scope}.log"
        report_data["log_prefix"] = str(log)
        if args.command == "doctor":
            print(f"Repository: {root}\nHost: {system} {platform.machine()}\nPython: {sys.version}\n"
                  f"Config: {cfg.file}\nTarget: {triplet}; host: {host}\nBuild: {workspace}\nInstall: {cfg.installed}\n"
                  f"Downloads: {cfg.downloads}\nFree disk: {shutil.disk_usage(workspace).free / 2**30:.1f} GiB")
            run([exe, "version"], root, env, log)
            run([cfg.cmake, "--version"], root, env, log.with_stem(log.stem + "-cmake"))
            if system == "Windows":
                if not (Path(cfg.vs_path) / "VC/Auxiliary/Build/vcvarsall.bat").is_file():
                    raise RuntimeError(f"VS_PATH has no C++ build environment: {cfg.vs_path}")
                print(f"Visual Studio: {cfg.vs_path}; toolset: {cfg.toolset}; generator: {cfg.generator}")
            else:
                run([cfg.gcc, "--version"], root, env, log.with_stem(log.stem + "-gcc"))
                run([cfg.gxx, "--version"], root, env, log.with_stem(log.stem + "-gxx"))
            audit(root, paths["reports"] / "source-inventory.json", cfg.file)
        elif args.command in {"plan", "build"}:
            triplets = write_triplet(cfg)
            manifest = write_manifest(root, cfg, args.port, manifest_file)
            if args.rebuild and (cfg.installed / "vcpkg/status").is_file():
                # 清单已保留全部现有包；强制重编目标及依赖它的包，再安装回同一 SDK。
                run([exe, "remove", f"{args.port}:{triplet}", "--classic", "--recurse",
                     f"--vcpkg-root={external}", f"--x-install-root={cfg.installed}",
                     f"--overlay-triplets={triplets}", f"--triplet={triplet}", f"--host-triplet={host}"],
                    root, env, log.with_stem(log.stem + "-remove"))
            # 安装库、构建树、暂存包和下载目录必须全部按编译器隔离。
            command = [exe, "install", f"--vcpkg-root={external}", f"--x-manifest-root={manifest}",
                       f"--overlay-ports={root / 'ports'}", f"--overlay-triplets={triplets}",
                       f"--triplet={triplet}", f"--host-triplet={host}",
                       f"--x-install-root={cfg.installed}", f"--x-buildtrees-root={paths['buildtrees']}",
                       f"--x-packages-root={paths['packages']}", f"--downloads-root={cfg.downloads}",
                       "--enforce-port-checks"]
            if args.stage == "native":
                command.append("--x-no-default-features")
            if args.from_source or args.rebuild:
                command.append("--binarysource=clear")
            if args.clean_buildtrees:
                command += ["--clean-buildtrees-after-build", "--clean-packages-after-build"]
            if args.command == "plan":
                command.append("--dry-run")
            run(command, root, env, log)
        elif args.command == "verify":
            installed = args.installed_root.resolve() if args.installed_root else cfg.installed
            report_data["installed_root"] = str(installed)
            verify(root, cfg, args, env, log, installed, jobs)
        else:
            from .licenses import collect
            report_data["scope"] = "actual installed packages; does not assert full manifest installation"
            report_data["installed_package_count"] = collect(
                root, cfg.installed / triplet, external, workspace / "reports/licenses")
        report_data["success"] = True
        report_data["completed_at"] = dt.datetime.now().isoformat(timespec="seconds")
        report.write_text(json.dumps(report_data, indent=2) + "\n", encoding="utf-8")
        return 0
    except (RuntimeError, OSError, ValueError, configparser.Error, subprocess.CalledProcessError) as error:
        if report is not None:
            report_data["success"] = False
            report_data["error"] = str(error)
            report.write_text(json.dumps(report_data, indent=2) + "\n", encoding="utf-8")
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
