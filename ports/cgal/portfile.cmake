set(VCPKG_BUILD_TYPE release)
vcpkg_from_github(OUT_SOURCE_PATH SOURCE_PATH
    REPO CGAL/cgal
    REF 28811b671a12b5caa9e3688569dadbc6b3728fe6
    SHA512 5597c3af28a7643da830e44b2d4aa866333e3d82eb70aead61414273e2388b819e9e9937889779cb418ac5fbb2cee97e74db43015822ae547fc9cc2888fd9b42
    PATCHES restricted-sdk.patch)
vcpkg_cmake_configure(SOURCE_PATH "${SOURCE_PATH}" OPTIONS
    -DBUILD_DOC=OFF -DCGAL_DEV_MODE=OFF -DCGAL_ENABLE_TESTING=OFF
    -DCGAL_ENABLE_CHECK_HEADERS=OFF -DCGAL_WITH_examples=OFF
    -DCGAL_WITH_demos=OFF -DCGAL_WITH_tests=OFF -DCGAL_WITH_benchmarks=OFF
    -DCGAL_TEST_DRAW_FUNCTIONS=OFF -DCGAL_DO_NOT_USE_BOOST_MP=OFF
    -DCGAL_INSTALL_INC_DIR=include -DCGAL_INSTALL_CMAKE_DIR=lib/cmake/CGAL
    -DCGAL_INSTALL_DOC_DIR=share/doc/CGAL)
vcpkg_cmake_install()
include("${CMAKE_CURRENT_LIST_DIR}/verify-inventory.cmake")
vcpkg_cmake_config_fixup(PACKAGE_NAME CGAL CONFIG_PATH lib/cmake/CGAL)
# This restricted package is header-only; config fixup can leave lib empty.
file(GLOB remaining_lib_entries "${CURRENT_PACKAGES_DIR}/lib/*")
if(NOT remaining_lib_entries)
    file(REMOVE_RECURSE "${CURRENT_PACKAGES_DIR}/lib")
endif()
if(EXISTS "${CURRENT_PACKAGES_DIR}/bin")
    file(COPY "${CURRENT_PACKAGES_DIR}/bin/" DESTINATION "${CURRENT_PACKAGES_DIR}/tools/cgal")
endif()
file(REMOVE_RECURSE "${CURRENT_PACKAGES_DIR}/bin" "${CURRENT_PACKAGES_DIR}/debug")
vcpkg_install_copyright(FILE_LIST "${SOURCE_PATH}/Installation/LICENSE"
    "${SOURCE_PATH}/Installation/LICENSE.LGPL" "${SOURCE_PATH}/Installation/LICENSE.GPL"
    "${SOURCE_PATH}/Installation/LICENSE.BSL" "${SOURCE_PATH}/Installation/LICENSE.CMAKE")
