"""Collect exact installed notices and SBOMs; never treat metadata as legal approval."""
import hashlib
import json
from pathlib import Path
import re
import shutil


def system_port_notice(prefix: Path, name: str, rule: dict, provenance: dict):
    """核对已审核的 Linux 空包，仅为 vcpkg 元数据/转接文件复用其 MIT 声明。"""
    manifests = list((prefix.parent / "vcpkg/info").glob(f"{name}_*_{prefix.name}.list"))
    if len(manifests) != 1:
        raise RuntimeError(f"Cannot verify system port file list: {name}")
    files = set()
    for line in manifests[0].read_text(encoding="utf-8").splitlines():
        if not line or line.endswith("/"):
            continue
        if not line.startswith(prefix.name + "/"):
            raise RuntimeError(f"Unexpected system port file path: {name}: {line}")
        files.add(line.removeprefix(prefix.name + "/"))
    # SBOM 还记录暂存包的 BUILD_INFO/CONTROL；vcpkg 不将它们安装到 SDK。
    staged_metadata = {"BUILD_INFO", "CONTROL"}
    files.update(item["fileName"].removeprefix("./") for item in provenance.get("files", [])
                 if item.get("SPDXID", "").startswith("SPDXRef-binary-file-")
                 and item["fileName"].removeprefix("./") not in staged_metadata)
    allowed = {f"share/{name}/vcpkg.spdx.json", f"share/{name}/vcpkg_abi_info.txt",
               *rule.get("allowed_payload", [])}
    unexpected = files - allowed
    if unexpected:
        raise RuntimeError(f"System port {name} contains unreviewed payload: {sorted(unexpected)}")
    if any(not (prefix / file).is_file() or (prefix / file).is_symlink() for file in files):
        raise RuntimeError(f"System port {name} has missing or linked payload files")
    notice = prefix / "share/vcpkg-cmake/copyright"
    if not notice.is_file():
        raise RuntimeError(f"Missing vcpkg MIT notice for system port: {name}")
    return notice, sorted(files)


def collect(root: Path, prefix: Path, external: Path, destination: Path):
    status = prefix.parent / "vcpkg/status"
    journals = sorted(p for p in (prefix.parent / "vcpkg/updates").glob("*") if p.is_file() and p.name.isdigit())
    database = ([status] if status.is_file() else []) + journals
    if not database:
        raise RuntimeError("No installed manifest SDK; build it before collecting notices")
    policy = json.loads((root / "docs/license-policy.json").read_text(encoding="utf-8"))
    destination.mkdir(parents=True, exist_ok=True)
    records, missing = [], []
    installed, features = [], {}
    # vcpkg may leave newer records in updates/ until its next invocation.
    # Merge in journal order, including removals and half-installed records.
    latest = {}
    for source in database:
        for paragraph in source.read_text(encoding="utf-8").split("\n\n"):
            fields = dict(line.split(": ", 1) for line in paragraph.splitlines() if ": " in line and not line.startswith(" "))
            if "Package" in fields:
                key = (fields["Package"], fields.get("Architecture"), fields.get("Feature", "core"))
                latest[key] = fields
    for fields in latest.values():
        if fields.get("Architecture") != prefix.name or fields.get("Status") != "install ok installed":
            continue
        if "Feature" in fields:
            features.setdefault(fields["Package"], []).append(fields["Feature"])
        else:
            installed.append(fields)
    if not installed:
        raise RuntimeError(f"No installed packages for {prefix.name}")
    for fields in installed:
        name = fields["Package"]
        share = prefix / "share" / name
        notice = share / "copyright"
        system_payload = None
        if not notice.is_file():
            # 官方空总包可明确复用其依赖的许可原文，仍检查文件是否存在。
            notice_port = policy.get(name, {}).get("copyright_port", name)
            notice = prefix / "share" / notice_port / "copyright"
        sbom = share / "vcpkg.spdx.json"
        provenance = json.loads(sbom.read_text(encoding="utf-8")) if sbom.exists() else {}
        system_rule = policy.get(name, {}).get("linux_system_port")
        if not notice.is_file() and system_rule and prefix.name.split("-")[1:2] == ["linux"]:
            notice, system_payload = system_port_notice(prefix, name, system_rule, provenance)
        available_notice = notice if notice.is_file() else root / "licenses" / name / "copyright"
        packages = provenance.get("packages", [])
        recipe = next((p for p in packages if p.get("SPDXID") == "SPDXRef-port"), {})
        binaries = [f["fileName"].removeprefix("./") for f in provenance.get("files", [])
                    if f.get("SPDXID", "").startswith("SPDXRef-binary-file-")]
        artifacts = {
            "shared_libraries": [f for f in binaries if re.search(r"\.(dll|pyd|dylib|so(?:\.[0-9.]+)?)$", f)],
            "archive_or_import_libraries": [f for f in binaries if f.endswith((".lib", ".a"))],
            "windows_executables": [f for f in binaries if f.endswith(".exe")],
            "tool_or_runtime_resource_directories": sorted({"/".join(f.split("/")[:2]) for f in binaries
                                                            if f.startswith(("tools/", "manual-tools/"))}),
        }
        entry = {"port": name, "version": recipe.get("versionInfo", fields.get("Version")),
                 "features": ["core", *sorted(features.get(name, []))],
                 "declared_license": recipe.get("licenseConcluded"), "policy": policy.get(name, {}),
                 "recipe_origin": recipe.get("downloadLocation"),
                 "artifacts": artifacts,
                 "sources": [p for p in packages if p.get("SPDXID", "").startswith("SPDXRef-resource-")],
                 "copyright": str(notice.relative_to(prefix)), "source_review": "required"}
        if system_payload is not None:
            entry["notice_scope"] = "vcpkg metadata/wrapper only; system implementation is not shipped by this port"
            entry["verified_system_port_files"] = system_payload
        supplemental_index = root / "licenses" / name / "index.json"
        if supplemental_index.exists():
            expected = json.loads(supplemental_index.read_text(encoding="utf-8")).get("source_version")
            actual = (entry["version"] or "").split("#", 1)[0]
            if expected and expected != actual:
                raise RuntimeError(f"Supplemental notices for {name} cover {expected}, installed {actual}; refresh the source review")
        if available_notice.is_file():
            target = destination / name
            target.mkdir(exist_ok=True)
            shutil.copy2(available_notice, target / "copyright")
            entry["copyright_source"] = "installed SDK" if available_notice == notice else "repository supplement: " + str(available_notice.relative_to(root))
            entry["copyright_sha256"] = hashlib.sha256(available_notice.read_bytes()).hexdigest()
            entry["additional_notices"] = []
            for extra in notice.parent.rglob("*"):
                if not extra.is_file() or extra == notice:
                    continue
                relative = extra.relative_to(notice.parent)
                license_directory = any(part.lower() in {"licenses", "licences", "notices", "copyrights"}
                                        for part in relative.parts[:-1])
                if license_directory or re.match(
                        r"(?:copyright|copying|licen[cs]e|notice|authors|gnu-[lag]*gpl|third.?party)",
                        extra.name, re.IGNORECASE):
                    copied = target / relative
                    copied.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(extra, copied)
                    entry["additional_notices"].append({"path": relative.as_posix(),
                        "sha256": hashlib.sha256(extra.read_bytes()).hexdigest()})
            if sbom.exists():
                shutil.copy2(sbom, target / "vcpkg.spdx.json")
                entry["sbom"] = name + "/vcpkg.spdx.json"
            supplements = root / "licenses" / name
            if supplements.is_dir():
                for extra in supplements.rglob("*"):
                    if extra.is_file():
                        relative = Path("supplemental") / extra.relative_to(supplements)
                        copied = target / relative
                        copied.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(extra, copied)
                        entry["additional_notices"].append({"path": relative.as_posix(),
                            "sha256": hashlib.sha256(extra.read_bytes()).hexdigest()})
        else:
            missing.append(name)
        records.append(entry)
    records.sort(key=lambda item: item["port"])
    (destination / "inventory.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Installed license inventory", "", "Exact installed notices and available vcpkg SBOMs are copied alongside this report.",
             "Metadata alone is not a distribution approval. Apply the obligations in docs/licensing.md to the actual application dependency closure.", "",
             "Windows .lib entries may be import libraries. The artifact list does not classify every .lib as static.", "",
             "| Port | Installed version | Shared files | Port metadata | Selected policy |", "| --- | --- | --- | --- | --- |"]
    for entry in records:
        lines.append(f"| {entry['port']} | {entry['version']} | {len(entry['artifacts']['shared_libraries'])} | {entry['declared_license'] or 'Review original notices'} | {entry['policy'].get('selection', 'Retain original notices; review bundled code')} |")
    (destination / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Collected notices for {len(records)} installed ports: {destination}")
    if missing:
        raise RuntimeError("Missing mandatory copyright files: " + ", ".join(missing))
    return len(records)
