"""选择依赖清单或单库；同一编译环境始终共用一套构建和安装目录。"""
import json
import re
import subprocess


def validate_selection(root, manifest_file, port=None):
    """校验用户选择，不改 config.ini 指定的任何输出目录。"""
    if not manifest_file.is_relative_to(root) or manifest_file.suffix != ".json":
        raise RuntimeError("--manifest must select a JSON file inside this repository")
    if manifest_file != root / "vcpkg.json" and not manifest_file.is_file():
        raise RuntimeError(f"Missing manifest: {manifest_file}")
    if port is not None and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", port):
        raise RuntimeError("--port requires a port name, for example tbb or pinocchio")


def installed_dependencies(config):
    """让 vcpkg 读取安装记录，保留已安装包的 features，避免缩小清单时误删。"""
    if not (config.installed / "vcpkg").is_dir():
        return []
    exe = config.vcpkg_root / ("vcpkg.exe" if config.system == "Windows" else "vcpkg")
    result = subprocess.run(
        [str(exe), "list", "--x-json", f"--vcpkg-root={config.vcpkg_root}",
         f"--x-install-root={config.installed}"],
        check=True, capture_output=True, text=True, encoding="utf-8")
    dependencies = []
    for package in json.loads(result.stdout).values():
        if package["triplet"] == config.triplet:
            dependencies.append({"name": package["package_name"], "default-features": False,
                                 "features": package["features"]})
    return dependencies


def write_manifest(root, config, port=None, manifest_file=None):
    """vcpkg 只识别名为 vcpkg.json 的清单，因此在构建目录中生成副本。"""
    manifest_file = manifest_file or root / "vcpkg.json"
    if not port and manifest_file == root / "vcpkg.json":
        return root
    original = json.loads(manifest_file.read_text(encoding="utf-8-sig"))
    manifest = original
    if port:
        dependencies = list(original.get("dependencies", []))
        for feature in original.get("features", {}).values():
            dependencies.extend(feature.get("dependencies", []))
        selected = [item for item in dependencies
                    if (item if isinstance(item, str) else item["name"]) == port]
        manifest = {"name": "selected-port", "version-string": "0",
                    "dependencies": selected or [port]}
        if "overrides" in original:
            manifest["overrides"] = original["overrides"]
    # 部分清单也安装到主 SDK；已有的其他包必须留在期望集合中。
    requested = manifest.get("dependencies", [])
    names = {item if isinstance(item, str) else item["name"] for item in requested}
    manifest["dependencies"] = requested + [
        item for item in installed_dependencies(config) if item["name"] not in names]
    configuration = json.loads((root / "vcpkg-configuration.json").read_text(encoding="utf-8"))
    # 生成清单位于临时目录，因此 overlay 路径需指回本仓库。
    configuration["overlay-ports"] = [str(root / "ports")]
    folder = config.build / "manifest"
    folder.mkdir(parents=True, exist_ok=True)
    for name, data in (("vcpkg.json", manifest), ("vcpkg-configuration.json", configuration)):
        (folder / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return folder
