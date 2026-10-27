"""读取用户的 config.ini，并生成 vcpkg 所需的最小 triplet。"""
import configparser
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class BuildConfig:
    file: Path
    system: str
    toolchain: str
    cpp_standard: str
    cpp_standard_overrides: dict[str, str]
    triplet: str
    build: Path
    installed: Path
    downloads: Path
    binary_cache: Path
    vcpkg_root: Path
    cmake: Path
    generator: str
    jobs: int
    vs_path: str
    gcc: str
    gxx: str
    library_path: str

    @property
    def toolset(self):
        # 用户沿用 vc143 的写法，MSBuild/vcpkg 的参数名为 v143。
        return self.toolchain.replace("vc", "v", 1)

    def paths(self):
        return {
            "build": self.build,
            "installed": self.installed,
            "downloads": self.downloads,
            "binary_cache": self.binary_cache,
            "buildtrees": self.build / "b",
            "packages": self.build / "p",
            "registries": self.build / "registries",
            "reports": self.build / "reports",
            "logs": self.build / "logs",
            "triplets": self.build / "triplets",
            "consumer": self.build / "consumer",
        }


def read_config(root: Path, file: Path, system: str) -> BuildConfig:
    """只读取选中的平台；不调用工具、不创建目录、不推测编译器安装位置。"""
    ini = configparser.ConfigParser(interpolation=None)
    if not ini.read(file, encoding="utf-8-sig"):
        raise RuntimeError(f"Missing {file}; copy config.ini.example to config.ini and edit it")
    section_name = "env_win" if system == "Windows" else "env_linux"
    if section_name not in ini:
        raise RuntimeError(f"Missing [{section_name}] in {file}")
    section = ini[section_name]
    toolchain = section.get("TOOLCHAIN", "").strip()
    standard = section.get("CPP_STANDARD", "").strip()
    pattern = r"vc[0-9]+" if system == "Windows" else r"gcc[0-9]+"
    if not re.fullmatch(pattern, toolchain):
        raise RuntimeError(f"[{section_name}] TOOLCHAIN must be vcNNN (Windows) or gccN (Linux)")
    if standard not in {"cpp20", "cpp23", "cpp26"}:
        raise RuntimeError("CPP_STANDARD must be cpp20, cpp23 or cpp26; consumers require C++20 or newer")

    # 只为已经确认不兼容的 port 设置较低标准，不因普通构建失败自动降级。
    overrides = {}
    allowed = {"cpp11", "cpp14", "cpp17", "cpp20", "cpp23"}
    if system == "Windows":
        allowed.remove("cpp11")  # MSVC 最低提供 /std:c++14。
    for item in section.get("CPP_STANDARD_OVERRIDES", "").split(","):
        if not item.strip():
            continue
        port, separator, fallback = (part.strip() for part in item.partition("="))
        if (not separator or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", port)
                or fallback not in allowed or int(fallback[3:]) >= int(standard[3:])):
            raise RuntimeError(f"[{section_name}] Invalid C++ fallback: {item}; use port=cpp17, port=cpp14")
        if port in overrides:
            raise RuntimeError(f"[{section_name}] Duplicate C++ fallback for {port}")
        overrides[port] = fallback

    def value(key, default=""):
        text = section.get(key, "").strip() or default
        return text.replace("${TOOLCHAIN}", toolchain).replace("${CPP_STANDARD}", standard)

    def path(key, default=""):
        text = value(key, default)
        if not text:
            raise RuntimeError(f"[{section_name}] {key} must be set explicitly")
        result = Path(text).expanduser()
        return result if result.is_absolute() else root / result

    tag = f"{toolchain}_{standard}"
    compiler = toolchain.replace("vc", "v", 1) if system == "Windows" else toolchain
    jobs = int(value("JOBS", "12"))
    if jobs < 1:
        raise RuntimeError("JOBS must be positive")
    generator = value("CMAKE_GENERATOR")
    if not generator:
        raise RuntimeError("CMAKE_GENERATOR must be set explicitly")
    if system == "Windows" and not generator.startswith("Visual Studio "):
        raise RuntimeError("Windows consumer verification currently requires a Visual Studio generator")
    return BuildConfig(
        file=file, system=system, toolchain=toolchain, cpp_standard=standard,
        cpp_standard_overrides=overrides,
        triplet=f"x64-{system.lower()}-{compiler}-{standard}",
        build=path("BUILD_DIR", f"build_{tag}"),
        installed=path("OUTPUT_DIR", f"install_{tag}"),
        downloads=path("DOWNLOAD_DIR", f"downloads_{tag}"),
        binary_cache=path("BINARY_CACHE_DIR", f"binary-cache_{tag}"),
        vcpkg_root=path("VCPKG_ROOT"), cmake=path("CMAKE_EXE"),
        generator=generator, jobs=jobs,
        vs_path=str(path("VS_PATH")) if system == "Windows" else "",
        gcc=str(path("GCC_EXE")) if system == "Linux" else "",
        gxx=str(path("GXX_EXE")) if system == "Linux" else "",
        library_path=value("LD_LIBRARY_PATH"),
    )


def output_directories(root: Path, file: Path):
    """源码审计排除两个平台的自定义产物目录；不要求另一平台已配好工具。"""
    ini = configparser.ConfigParser(interpolation=None)
    ini.read(file, encoding="utf-8-sig")
    result = []
    for section in ini.values():
        for key in ("BUILD_DIR", "OUTPUT_DIR", "DOWNLOAD_DIR", "BINARY_CACHE_DIR"):
            text = section.get(key, "").strip()
            if text:
                text = text.replace("${TOOLCHAIN}", section.get("TOOLCHAIN", ""))
                text = text.replace("${CPP_STANDARD}", section.get("CPP_STANDARD", ""))
                path = Path(text).expanduser()
                result.append((root / path).resolve())
    return result


def cmake_setting(name, value):
    """生成带引号的 CMake 字符串，兼容路径中的空格和反斜杠。"""
    escaped = str(value).replace("\\", "/").replace('"', '\\"').replace("$", "\\$")
    return f'set({name} "{escaped}")\n'


def write_triplet(config: BuildConfig) -> Path:
    """配置文件是唯一来源；生成文件位于所选 BUILD_DIR，不修改源码树。"""
    folder = config.build / "triplets"
    folder.mkdir(parents=True, exist_ok=True)
    # 每个例外单独计入对应 port 的 ABI，调整一个库不再改变整份 triplet。
    standards = folder / "cxx-standards"
    standards.mkdir(exist_ok=True)
    # 编译兼容修正经已有的逐 port 文件加载，避免改动公共 triplet
    # 导致整个 SDK 的 ABI 变化；脚本只计入对应 port 的构建标识。
    standard_fixes = ({"icu": Path(__file__).resolve().parent / "port-fixes/icu-cxx-standard.cmake"}
                      if config.system == "Windows" else {
                          "octomap": Path(__file__).resolve().parent / "port-fixes/octomap.cmake",
                          "qtbase": Path(__file__).resolve().parent / "port-fixes/qtbase.cmake"})
    configured_ports = config.cpp_standard_overrides.keys() | standard_fixes.keys()
    for path in standards.glob("*.cmake"):
        if path.stem not in configured_ports:
            path.unlink()
    for port in sorted(configured_ports):
        standard = config.cpp_standard_overrides.get(port, config.cpp_standard)
        contents = cmake_setting("SDK_CXX_STANDARD", standard[3:])
        if port in standard_fixes:
            contents += cmake_setting("SDK_PORT_STANDARD_FIX", standard_fixes[port])
            contents += ('list(APPEND VCPKG_HASH_ADDITIONAL_FILES "${SDK_PORT_STANDARD_FIX}")\n'
                         'include("${SDK_PORT_STANDARD_FIX}")\n')
        (standards / f"{port}.cmake").write_text(contents, encoding="utf-8")
    triplet = "# Generated from config.ini; edit the INI, not this file.\n"
    triplet += cmake_setting("VCPKG_TARGET_ARCHITECTURE", "x64")
    triplet += cmake_setting("VCPKG_CRT_LINKAGE", "dynamic")
    triplet += cmake_setting("VCPKG_LIBRARY_LINKAGE", "dynamic")
    triplet += cpp_standard_settings(config)
    if config.system == "Windows":
        triplet += cmake_setting("VCPKG_PLATFORM_TOOLSET", config.toolset)
        triplet += cmake_setting("VCPKG_VISUAL_STUDIO_PATH", config.vs_path)
        triplet += "file(TO_NATIVE_PATH \"${VCPKG_VISUAL_STUDIO_PATH}\" VCPKG_VISUAL_STUDIO_PATH)\n"
        triplet += "set(VCPKG_PROVIDED_FORTRAN ON)\n"
    else:
        toolchain = folder / "linux-toolchain.cmake"
        contents = cmake_setting("CMAKE_C_COMPILER", config.gcc)
        contents += cmake_setting("CMAKE_CXX_COMPILER", config.gxx)
        contents += cmake_setting("CMAKE_ASM_COMPILER", config.gcc)
        contents += cmake_setting("SDK_VCPKG_LINUX_TOOLCHAIN", config.vcpkg_root / "scripts/toolchains/linux.cmake")
        contents += 'include("${SDK_VCPKG_LINUX_TOOLCHAIN}")\n'
        toolchain.write_text(contents, encoding="utf-8")
        triplet += "set(VCPKG_CMAKE_SYSTEM_NAME Linux)\nset(VCPKG_FIXUP_ELF_RPATH ON)\n"
        triplet += cmake_setting("VCPKG_CHAINLOAD_TOOLCHAIN_FILE", toolchain)
        fixes = Path(__file__).resolve().parent / "port-fixes"
        triplet += cmake_setting("SDK_PORT_FIXES", fixes)
        triplet += '''if(PORT STREQUAL "at-spi2-core")
    list(APPEND VCPKG_HASH_ADDITIONAL_FILES "${SDK_PORT_FIXES}/at-spi2-core.cmake")
    include("${SDK_PORT_FIXES}/at-spi2-core.cmake")
elseif(PORT STREQUAL "ompl" OR PORT STREQUAL "vtk")
    list(APPEND VCPKG_POST_PORTFILE_INCLUDES "${SDK_PORT_FIXES}/remove-empty-bin.cmake")
endif()
'''
    (folder / f"{config.triplet}.cmake").write_text(triplet, encoding="utf-8")
    return folder


def cpp_standard_settings(config: BuildConfig) -> str:
    """CMake 与其他构建系统共用标准；例外只作用于当前 port。"""
    text = cmake_setting("SDK_CXX_STANDARD", config.cpp_standard[3:])
    text += '''set(SDK_PORT_STANDARD "${CMAKE_CURRENT_LIST_DIR}/cxx-standards/${PORT}.cmake")
if(EXISTS "${SDK_PORT_STANDARD}")
    include("${SDK_PORT_STANDARD}")
    list(APPEND VCPKG_HASH_ADDITIONAL_FILES "${SDK_PORT_STANDARD}")
endif()
'''
    if config.system == "Windows":
        text += '''if(SDK_CXX_STANDARD GREATER 20)
    set(VCPKG_CXX_FLAGS "/std:c++latest")
else()
    set(VCPKG_CXX_FLAGS "/std:c++${SDK_CXX_STANDARD}")
endif()
'''
    else:
        text += 'set(VCPKG_CXX_FLAGS "-std=c++${SDK_CXX_STANDARD}")\n'
    # vcpkg 要求 C_FLAGS 与 CXX_FLAGS 同时定义；C 库不受 C++ 标准影响。
    text += 'set(VCPKG_C_FLAGS "")\n'
    hook = Path(__file__).resolve().parent / "cmake/cxx-standard.cmake"
    text += cmake_setting("SDK_CXX_STANDARD_HOOK", hook)
    text += '''list(APPEND VCPKG_HASH_ADDITIONAL_FILES "${SDK_CXX_STANDARD_HOOK}")
list(APPEND VCPKG_CMAKE_CONFIGURE_OPTIONS
    "-DCMAKE_CXX_STANDARD=${SDK_CXX_STANDARD}"
    "-DCMAKE_CXX_STANDARD_REQUIRED=ON"
    "-DCMAKE_CXX_EXTENSIONS=OFF"
    "-DSDK_CXX_STANDARD=${SDK_CXX_STANDARD}"
    "-DCMAKE_PROJECT_TOP_LEVEL_INCLUDES=${SDK_CXX_STANDARD_HOOK}")
'''
    fmt_options = Path(__file__).resolve().parent / "port-fixes/fmt.cmake"
    text += 'if(PORT STREQUAL "fmt")\n'
    text += "    " + cmake_setting("SDK_FMT_OPTIONS", fmt_options)
    text += '''    list(APPEND VCPKG_HASH_ADDITIONAL_FILES "${SDK_FMT_OPTIONS}")
    include("${SDK_FMT_OPTIONS}")
endif()
'''
    return text
