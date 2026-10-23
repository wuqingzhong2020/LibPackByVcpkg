# CPython 使用上游构建系统；九个公共 C 库由 vcpkg 管理。
vcpkg_check_linkage(ONLY_DYNAMIC_LIBRARY)
if(VCPKG_CROSSCOMPILING)
    message(FATAL_ERROR "python3 currently supports native x64 Windows/Linux builds only")
endif()

vcpkg_from_github(
    OUT_SOURCE_PATH SOURCE_PATH
    REPO python/cpython
    REF "v${VERSION}"
    SHA512 27fbe02a1742c0e329350167d744d612c2f8d140ed73247c24599e02dc3f2dd5f213ff5ee9e3d0a60ed8e84f06c4a4f30fb31a4ea4e570b61a03f355dfb34b74
    PATCHES external-libraries.patch public-libraries.patch
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
