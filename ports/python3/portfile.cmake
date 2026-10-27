# CPython 使用上游构建系统；九个公共 C 库由 vcpkg 管理。
vcpkg_check_linkage(ONLY_DYNAMIC_LIBRARY)
if(VCPKG_CROSSCOMPILING)
    message(FATAL_ERROR "python3 currently supports native x64 Windows/Linux builds only")
endif()

vcpkg_from_github(
    OUT_SOURCE_PATH SOURCE_PATH
    REPO python/cpython
    REF "v${VERSION}"
    SHA512 c57f79ec1f620790216d72b3aff74b299fe107939b5e1846687a1fc91dea373a90da17968b770a99f3a37f0d5e0da754af2f95690c0af409892ec0f73eb29282
    PATCHES public-libraries.patch
)
vcpkg_find_acquire_program(PYTHON3)
unset(ENV{PYTHONHOME})
unset(ENV{PYTHONPATH})
unset(ENV{PYTHON_HEXVERSION})

if(VCPKG_TARGET_IS_WINDOWS)
    include("${CURRENT_PORT_DIR}/windows.cmake")
else()
    include("${CURRENT_PORT_DIR}/linux.cmake")
endif()

configure_file("${CURRENT_PORT_DIR}/cpython-config.cmake.in"
    "${CURRENT_PACKAGES_DIR}/share/cpython/cpython-config.cmake" @ONLY)
vcpkg_install_copyright(FILE_LIST
    "${SOURCE_PATH}/LICENSE"
    "${SOURCE_PATH}/Modules/_hacl/Hacl_Hash_SHA2.h"
    "${SOURCE_PATH}/Modules/_hacl/include/krml/internal/target.h"
    "${SOURCE_PATH}/Modules/expat/COPYING"
    "${SOURCE_PATH}/Doc/license.rst"
)
