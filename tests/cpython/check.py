"""Exercise public C dependencies from the interpreter and a C++ embedding host."""
import bz2
import ctypes
import decimal
import hashlib
import importlib.util
import lzma
import os
from pathlib import Path
import pyexpat
import sqlite3
import ssl
import sys
import sysconfig
import xml.etree.ElementTree as ET
import zlib
from compression import zstd
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

assert sys.version_info[:3] == (3, 15, 0), sys.version
assert hasattr(sys, "gettotalrefcount") == (os.environ["SDK_EXPECTED_CONFIG"] == "Debug")
assert sysconfig.get_config_var("Py_GIL_DISABLED") == 1
assert not sys._is_gil_enabled()
for disabled in ("_tkinter", "readline"):
    assert importlib.util.find_spec(disabled) is None, disabled

sys.path.insert(0, sys.argv[1])
import sdk_cpython_extension
assert sdk_cpython_extension.answer() == 42

payload = ("CPython SDK 压缩与数据库\n" * 1000).encode()
for codec in (zlib, bz2, lzma, zstd):
    assert codec.decompress(codec.compress(payload)) == payload, codec.__name__

# A real libffi call and callback, not merely an import of ctypes.
callback_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
callback = callback_type(lambda x: x + 1)
assert callback(41) == 42
assert decimal.Decimal("0.1") + decimal.Decimal("0.2") == decimal.Decimal("0.3")

with closing(sqlite3.connect(":memory:")) as db:
    db.execute("CREATE TABLE example (value TEXT)")
    db.execute("INSERT INTO example VALUES (?)", ("中文 SQLite",))
    assert db.execute("SELECT value FROM example").fetchone()[0] == "中文 SQLite"
    with closing(sqlite3.connect(":memory:")) as copy:
        copy.deserialize(db.serialize())
        assert copy.execute("SELECT count(*) FROM example").fetchone()[0] == 1

parsed = []
parser = pyexpat.ParserCreate()
parser.StartElementHandler = lambda name, attrs: parsed.append(name)
parser.Parse(b"<sdk><python/></sdk>", True)
assert parsed == ["sdk", "python"]
assert ET.fromstring("<sdk><python>42</python></sdk>").findtext("python") == "42"
assert type(hashlib.sha256()).__module__ == "_hashlib"
assert hashlib.pbkdf2_hmac("sha256", b"password", b"salt", 1).hex() == (
    "120fb6cffcf8b32c43e7225256c4f837a86548c92ccc35480805987cb70be17b"
)

# Start TLS locally using MemoryBIO: exercise OpenSSL without external network.
context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
incoming, outgoing = ssl.MemoryBIO(), ssl.MemoryBIO()
connection = context.wrap_bio(incoming, outgoing, server_hostname="localhost")
try:
    connection.do_handshake()
except ssl.SSLWantReadError:
    pass
else:
    raise AssertionError("A TLS client must wait for the server")
assert outgoing.read().startswith(b"\x16\x03"), "Missing TLS ClientHello"

def worker(index):
    packed = zstd.compress(payload + str(index).encode())
    return zstd.decompress(packed) == payload + str(index).encode()

with ThreadPoolExecutor(max_workers=4) as pool:
    assert all(pool.map(worker, range(32)))
assert not sys._is_gil_enabled(), "An extension enabled the GIL"

# Verify the loaded libraries actually came from this SDK, including Debug.
prefix = Path(os.environ["SDK_EXPECTED_PREFIX"]).resolve()
config_prefix = prefix / "debug" if os.environ["SDK_EXPECTED_CONFIG"] == "Debug" else prefix
if sys.platform == "win32":
    debug = os.environ["SDK_EXPECTED_CONFIG"] == "Debug"
    names = ["ffi-8.dll", "libmpdec-4.0.1.dll", "zd.dll" if debug else "z.dll",
             "bz2d.dll" if debug else "bz2.dll", "libexpatd.dll" if debug else "libexpat.dll",
             "liblzma.dll", "sqlite3.dll", "zstd.dll", "libssl-3-x64.dll", "libcrypto-3-x64.dll"]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
    kernel.GetModuleHandleW.restype = ctypes.c_void_p
    kernel.GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint]
    kernel.GetModuleFileNameW.restype = ctypes.c_uint
    for name in names:
        handle = kernel.GetModuleHandleW(name)
        assert handle, (name, ctypes.get_last_error())
        buffer = ctypes.create_unicode_buffer(32768)
        assert kernel.GetModuleFileNameW(handle, buffer, len(buffer))
        path = Path(buffer.value).resolve()
        allowed = [config_prefix / "bin", prefix / "tools/python3" / ("debug" if debug else "")]
        assert any(path.is_relative_to(base) for base in allowed), path
else:
    # The pathname is the sixth field and may itself contain spaces.
    mappings = (line.split(maxsplit=5) for line in Path("/proc/self/maps").read_text().splitlines())
    loaded = {Path(fields[5]).resolve() for fields in mappings
              if len(fields) == 6 and fields[5].startswith("/")}
    bzip2_name = "libbz2d.so" if os.environ["SDK_EXPECTED_CONFIG"] == "Debug" else "libbz2.so"
    for name in ("libffi.so", "libmpdec.so", "libz.so", bzip2_name, "libexpat.so",
                 "liblzma.so", "libsqlite3.so", "libzstd.so", "libssl.so", "libcrypto.so"):
        matches = [path for path in loaded if path.name.startswith(name)]
        assert matches, name
        assert all(path.is_relative_to(config_prefix / "lib") for path in matches), matches

print(f"PASS {sys.version.split()[0]} {os.environ['SDK_EXPECTED_CONFIG']}; "
      f"{ssl.OPENSSL_VERSION}; SQLite {sqlite3.sqlite_version}; {pyexpat.EXPAT_VERSION}; "
      f"zstd {zstd.zstd_version}; GIL={sys._is_gil_enabled()}; no Tk/Readline")
