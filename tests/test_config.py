"""验证 INI 到构建命令的传递；所有外部命令均模拟，不启动编译。"""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import cli
from scripts.config import read_config, write_triplet
from scripts.manifest import validate_selection, write_manifest


SETTINGS = """
[env_win]
TOOLCHAIN = vc143
CPP_STANDARD = cpp20
VCPKG_ROOT = tools/vcpkg
VS_PATH = tools/Visual Studio
CMAKE_EXE = tools/cmake/bin/cmake.exe
CMAKE_GENERATOR = Visual Studio 17 2022
JOBS = 3

[env_linux]
TOOLCHAIN = gcc16
CPP_STANDARD = cpp20
VCPKG_ROOT = tools/vcpkg
GCC_EXE = tools/gcc/bin/gcc-16
GXX_EXE = tools/gcc/bin/g++-16
CMAKE_EXE = tools/cmake/bin/cmake
CMAKE_GENERATOR = Ninja
LD_LIBRARY_PATH = /opt/gcc/lib64:/opt/gcc/lib
JOBS = 5
"""


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.file = self.root / "config.ini"
        self.file.write_text(SETTINGS, encoding="utf-8")

    def test_platforms_and_future_compilers_have_separate_outputs(self):
        configs = [read_config(self.root, self.file, system) for system in ("Windows", "Linux")]
        self.file.write_text(SETTINGS.replace("vc143", "vc145").replace("gcc16", "gcc15")
                            .replace("cpp20", "cpp23"), encoding="utf-8")
        configs += [read_config(self.root, self.file, system) for system in ("Windows", "Linux")]
        self.assertEqual([cfg.build.name for cfg in configs],
                         ["build_vc143_cpp20", "build_gcc16_cpp20", "build_vc145_cpp23", "build_gcc15_cpp23"])
        for first in configs:
            for second in configs:
                if first is not second:
                    self.assertTrue(set(first.paths().values()).isdisjoint(second.paths().values()))

    def test_custom_directories_and_unconfigured_other_platform(self):
        text = SETTINGS.split("[env_linux]")[0]
        text += "BUILD_DIR = scratch/${TOOLCHAIN}_${CPP_STANDARD}\nOUTPUT_DIR = sdk/${TOOLCHAIN}\n"
        text += f"DOWNLOAD_DIR = {self.root / 'shared archives'}\n[env_linux]\n"
        self.file.write_text(text, encoding="utf-8-sig")
        cfg = read_config(self.root, self.file, "Windows")
        self.assertEqual(cfg.build, self.root / "scratch/vc143_cpp20")
        self.assertEqual(cfg.installed, self.root / "sdk/vc143")
        self.assertEqual(cfg.downloads, self.root / "shared archives")
        for directory in (cfg.build, cfg.installed, cfg.downloads):
            directory.mkdir(parents=True)
            (directory / "generated.txt").touch()
        (self.root / "source.cpp").touch()
        report = cfg.build / "reports/source-inventory.json"
        with contextlib.redirect_stdout(io.StringIO()):
            cli.audit(self.root, report, self.file)
        self.assertEqual(list(json.loads(report.read_text(encoding="utf-8"))), ["source.cpp"])

    def test_missing_compiler_is_an_error_not_a_default(self):
        for key in ("TOOLCHAIN = vc143", "VS_PATH = tools/Visual Studio"):
            self.file.write_text(SETTINGS.replace(key, key.split("=")[0] + "="), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                read_config(self.root, self.file, "Windows")

    def test_generated_triplets_use_explicit_compilers(self):
        for system in ("Windows", "Linux"):
            cfg = read_config(self.root, self.file, system)
            folder = write_triplet(cfg)
            triplet = (folder / f"{cfg.triplet}.cmake").read_text(encoding="utf-8")
            if system == "Windows":
                self.assertIn('set(VCPKG_PLATFORM_TOOLSET "v143")', triplet)
                self.assertIn(cfg.vs_path.replace("\\", "/"), triplet)
            else:
                toolchain = (folder / "linux-toolchain.cmake").read_text(encoding="utf-8")
                self.assertIn(cfg.gcc.replace("\\", "/"), toolchain)
                self.assertIn(cfg.gxx.replace("\\", "/"), toolchain)
                self.assertIn("scripts/toolchains/linux.cmake", toolchain)

    def test_commands_take_paths_tools_and_standard_from_ini(self):
        external_temp = tempfile.TemporaryDirectory()
        self.addCleanup(external_temp.cleanup)
        (self.root / "vcpkg-configuration.json").write_text(
            json.dumps({"default-registry": {"baseline": "test-baseline"}}), encoding="utf-8")
        for system in ("Windows", "Linux"):
            # Absolute BUILD_DIR outside the source root must also work for logs/reports.
            self.file.write_text(SETTINGS.replace("cpp20", "cpp23").replace(
                "JOBS =", f"BUILD_DIR = {external_temp.name}/${{TOOLCHAIN}}\nJOBS ="),
                encoding="utf-8")
            cfg = read_config(self.root, self.file, system)
            cfg.vcpkg_root.mkdir(parents=True, exist_ok=True)
            (cfg.vcpkg_root / ("vcpkg.exe" if system == "Windows" else "vcpkg")).touch()
            for command in ("plan", "build", "verify", "licenses"):
                with (
                    self.subTest(system=system, command=command),
                    patch("sys.argv", ["build.py", command]),
                    patch.object(cli.platform, "system", return_value=system),
                    patch.object(cli.subprocess, "run"),
                    patch.object(cli, "run") as run,
                    patch("scripts.licenses.collect", return_value=1) as collect,
                    contextlib.redirect_stdout(io.StringIO()),
                ):
                    self.assertEqual(cli.main(self.root), 0)
                    if command in {"plan", "build"}:
                        arguments, _, env, log = run.call_args.args
                        for flag, path in (("--x-install-root", cfg.installed),
                                           ("--x-buildtrees-root", cfg.build / "b"),
                                           ("--x-packages-root", cfg.build / "p"),
                                           ("--downloads-root", cfg.downloads),
                                           ("--overlay-triplets", cfg.build / "triplets")):
                            self.assertIn(f"{flag}={path}", arguments)
                        self.assertEqual(env["VCPKG_REGISTRIES_CACHE"], str(cfg.build / "registries"))
                        self.assertEqual(env["VCPKG_DEFAULT_BINARY_CACHE"], str(cfg.binary_cache))
                        self.assertEqual(log.parent, cfg.build / "logs")
                        self.assertEqual("--dry-run" in arguments, command == "plan")
                        if system == "Linux":
                            self.assertEqual((env["CC"], env["CXX"]), (cfg.gcc, cfg.gxx))
                    elif command == "verify":
                        self.assertEqual(run.call_count, 6)
                        arguments = run.call_args_list[0].args[0]
                        self.assertEqual(arguments[0], cfg.cmake)
                        self.assertIn(f"-DVCPKG_INSTALLED_DIR={cfg.installed}", arguments)
                        self.assertIn("-DCMAKE_CXX_STANDARD=23", arguments)
                        self.assertIn(cfg.generator, arguments)
                    else:
                        self.assertEqual(collect.call_args.args[1], cfg.installed / cfg.triplet)

    def test_paths_only_reads_config(self):
        with (
            patch("sys.argv", ["build.py", "paths"]),
            patch.object(cli.platform, "system", return_value="Windows"),
            patch.object(cli.subprocess, "run") as subprocess_run,
            patch.object(cli, "run") as run,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(cli.main(self.root), 0)
        run.assert_not_called()
        subprocess_run.assert_not_called()
        self.assertEqual(list(self.root.iterdir()), [self.file])

    def test_python_only_verification_does_not_install_the_full_sdk(self):
        (self.root / "vcpkg.json").write_text('{"dependencies": ["python3"]}', encoding="utf-8")
        (self.root / "vcpkg-configuration.json").write_text(
            json.dumps({"default-registry": {"baseline": "test-baseline"}}), encoding="utf-8")
        for system in ("Windows", "Linux"):
            cfg = read_config(self.root, self.file, system)
            cfg.vcpkg_root.mkdir(parents=True, exist_ok=True)
            (cfg.vcpkg_root / ("vcpkg.exe" if system == "Windows" else "vcpkg")).touch()
            with (
                self.subTest(system=system),
                patch("sys.argv", ["build.py", "verify", "--port", "python3"]),
                patch.object(cli.platform, "system", return_value=system),
                patch.object(cli.subprocess, "run"),
                patch.object(cli, "run") as run,
                patch.object(cli, "write_manifest") as manifest,
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(cli.main(self.root), 0)
                manifest.assert_not_called()
                self.assertEqual(run.call_count, 6)
                for call in (run.call_args_list[0], run.call_args_list[3]):
                    args = call.args[0]
                    self.assertEqual(args[args.index("-S") + 1], self.root / "tests/cpython")
                    self.assertIn("-DVCPKG_MANIFEST_INSTALL=OFF", args)
                self.assertTrue((cfg.build / "reports/verify-python3.json").is_file())

    def test_single_manifest_keeps_features_baseline_and_overrides(self):
        original = {"dependencies": ["tbb"], "features": {"custom": {
            "dependencies": [{"name": "pinocchio", "features": ["urdf"]}]}},
            "overrides": [{"name": "example", "version": "1.0.0"}]}
        source = self.root / "vcpkg.json"
        source.write_text(json.dumps(original), encoding="utf-8")
        configuration = {"default-registry": {"kind": "builtin", "baseline": "test-baseline"},
                         "overlay-ports": ["ports"]}
        (self.root / "vcpkg-configuration.json").write_text(json.dumps(configuration), encoding="utf-8")
        cfg = read_config(self.root, self.file, "Windows")
        folder = write_manifest(self.root, cfg, "pinocchio")
        manifest = json.loads((folder / "vcpkg.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["dependencies"], [{"name": "pinocchio", "features": ["urdf"]}])
        self.assertEqual(manifest["overrides"], original["overrides"])
        generated = json.loads((folder / "vcpkg-configuration.json").read_text(encoding="utf-8"))
        self.assertEqual(generated["default-registry"], configuration["default-registry"])
        self.assertEqual(json.loads(source.read_text(encoding="utf-8")), original)

    def test_single_rebuild_uses_selected_ini_and_shared_sdk(self):
        custom = self.root / "config.another.ini"
        custom.write_text(SETTINGS.replace("vc143", "vc145"), encoding="utf-8")
        base = read_config(self.root, custom, "Windows")
        cfg = base
        base.vcpkg_root.mkdir(parents=True)
        (base.vcpkg_root / "vcpkg.exe").touch()
        (cfg.installed / "vcpkg").mkdir(parents=True)
        (cfg.installed / "vcpkg/status").write_text("installed record", encoding="utf-8")
        installed = {"qtbase": {"package_name": "qtbase", "triplet": cfg.triplet,
                                "features": ["widgets"]}}
        (self.root / "vcpkg.json").write_text('{"dependencies": ["tbb", "qtbase"]}', encoding="utf-8")
        (self.root / "vcpkg-configuration.json").write_text(
            '{"default-registry": {"kind": "builtin", "baseline": "test-baseline"}}', encoding="utf-8")
        with (
            patch("sys.argv", ["build.py", "build", "--port", "tbb", "--rebuild", "-c", str(custom)]),
            patch.object(cli.platform, "system", return_value="Windows"),
            patch.object(cli.subprocess, "run", return_value=cli.subprocess.CompletedProcess(
                [], 0, stdout=json.dumps(installed))),
            patch.object(cli, "run") as run,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(cli.main(self.root), 0)
        remove, install = [call.args[0] for call in run.call_args_list]
        self.assertIn("remove", remove)
        self.assertIn("--recurse", remove)
        self.assertIn("tbb:x64-windows-v145-cpp20", remove)
        self.assertIn(f"--x-install-root={cfg.installed}", remove)
        self.assertIn(f"--x-install-root={cfg.installed}", install)
        self.assertIn("--binarysource=clear", install)
        self.assertIn(f"--x-install-root={base.installed}", remove)
        manifest = json.loads((cfg.build / "manifest/vcpkg.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["dependencies"], [
            "tbb", {"name": "qtbase", "default-features": False, "features": ["widgets"]}])
        self.assertEqual((base.installed / "vcpkg/status").read_text(encoding="utf-8"), "installed record")

    def test_invalid_port_names_are_rejected(self):
        for name in ("../tbb", "tbb[core]", "tbb:x64-linux", ""):
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                validate_selection(self.root, self.root / "vcpkg.json", name)


if __name__ == "__main__":
    unittest.main()
