"""Linux 系统接口空包不能掩盖实际第三方代码缺少许可的问题。"""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from scripts.licenses import collect


class LicenseCollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir()
        policy = {"libiconv": {"linux_system_port": {
            "allowed_payload": ["share/iconv/vcpkg-cmake-wrapper.cmake"]}}}
        (self.root / "docs/license-policy.json").write_text(json.dumps(policy), encoding="utf-8")
        self.prepare_sdk("x64-linux-gcc16-cpp20")

    def prepare_sdk(self, triplet):
        self.prefix = self.root / "installed" / triplet
        share = self.prefix / "share"
        for name in ("libiconv", "iconv", "vcpkg-cmake"):
            (share / name).mkdir(parents=True)
        (share / "vcpkg-cmake/copyright").write_text("vcpkg MIT notice\n", encoding="utf-8")
        (share / "iconv/vcpkg-cmake-wrapper.cmake").write_text("# vcpkg wrapper\n", encoding="utf-8")
        (share / "libiconv/vcpkg_abi_info.txt").write_text("abi\n", encoding="utf-8")
        spdx = {"packages": [{"SPDXID": "SPDXRef-port", "versionInfo": "1.19"}], "files": [
            {"SPDXID": "SPDXRef-binary-file-0", "fileName": "./BUILD_INFO"}]}
        (share / "libiconv/vcpkg.spdx.json").write_text(json.dumps(spdx), encoding="utf-8")
        info = self.prefix.parent / "vcpkg/info"
        info.mkdir(parents=True, exist_ok=True)
        self.manifest = info / f"libiconv_1.19_{triplet}.list"
        self.manifest.write_text("\n".join(f"{triplet}/{path}" for path in (
            "share/libiconv/vcpkg.spdx.json", "share/libiconv/vcpkg_abi_info.txt",
            "share/iconv/vcpkg-cmake-wrapper.cmake")) + "\n", encoding="utf-8")
        (info.parent / "status").write_text(
            f"Package: libiconv\nVersion: 1.19\nArchitecture: {triplet}\n"
            "Status: install ok installed\n\n", encoding="utf-8")

    def run_collect(self):
        destination = self.root / "reports"
        with contextlib.redirect_stdout(io.StringIO()):
            count = collect(self.root, self.prefix, self.root / "vcpkg", destination)
        return count, json.loads((destination / "inventory.json").read_text(encoding="utf-8"))[0]

    def test_verified_linux_wrapper_records_the_scope_of_the_mit_notice(self):
        count, entry = self.run_collect()
        self.assertEqual(count, 1)
        self.assertEqual(Path(entry["copyright"]).as_posix(), "share/vcpkg-cmake/copyright")
        self.assertIn("system implementation is not shipped", entry["notice_scope"])
        self.assertIn("share/iconv/vcpkg-cmake-wrapper.cmake", entry["verified_system_port_files"])
        self.assertEqual((self.root / "reports/libiconv/copyright").read_text(), "vcpkg MIT notice\n")

    def test_library_and_header_payload_cannot_borrow_the_wrapper_notice(self):
        original = self.manifest.read_text(encoding="utf-8")
        for name in ("lib/libiconv.so", "include/iconv.h"):
            with self.subTest(payload=name):
                payload = self.prefix / name
                payload.parent.mkdir(exist_ok=True)
                payload.write_text("unreviewed vendor code\n", encoding="utf-8")
                self.manifest.write_text(original + f"{self.prefix.name}/{name}\n", encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "unreviewed payload"):
                    self.run_collect()
                self.manifest.write_text(original, encoding="utf-8")
                payload.unlink()

    def test_windows_cannot_use_the_linux_wrapper_exception(self):
        self.prepare_sdk("x64-windows-v143-cpp20")
        with self.assertRaisesRegex(RuntimeError, "Missing mandatory copyright files: libiconv"):
            self.run_collect()

    def test_sbom_payload_is_checked_even_if_the_file_list_omits_it(self):
        spdx_file = self.prefix / "share/libiconv/vcpkg.spdx.json"
        spdx = json.loads(spdx_file.read_text(encoding="utf-8"))
        spdx["files"].append({"SPDXID": "SPDXRef-binary-file-1", "fileName": "./lib/libiconv.so"})
        spdx_file.write_text(json.dumps(spdx), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "unreviewed payload"):
            self.run_collect()

    def test_a_real_library_keeps_its_own_license_notice(self):
        notice = self.prefix / "share/libiconv/copyright"
        notice.write_text("GNU libiconv LGPL notice\n", encoding="utf-8")
        library = self.prefix / "lib/libiconv.so"
        library.parent.mkdir()
        library.write_text("vendor runtime library\n", encoding="utf-8")
        with self.manifest.open("a", encoding="utf-8") as manifest:
            manifest.write(f"{self.prefix.name}/lib/libiconv.so\n")
        _, entry = self.run_collect()
        self.assertEqual(Path(entry["copyright"]).as_posix(), "share/libiconv/copyright")
        self.assertNotIn("notice_scope", entry)
        self.assertEqual((self.root / "reports/libiconv/copyright").read_text(), notice.read_text())


if __name__ == "__main__":
    unittest.main()
