vcpkg_check_linkage(ONLY_DYNAMIC_LIBRARY)
vcpkg_from_github(
    OUT_SOURCE_PATH SOURCE_PATH
    REPO paceholder/nodeeditor
    REF 7c6341a66a8e46b8988140b9e60d892b6a3560b3
    SHA512 7c737df98f083a40a763c375d3c35714f39cf15baa63914d8281e6eecaf6a6eb4173d042d5a158ea6b5b7cd7a7b949e7ccd82df5e0eab9d09cb5cd074887ba58
    PATCHES sdk.patch
)
vcpkg_cmake_configure(
    SOURCE_PATH "${SOURCE_PATH}"
    OPTIONS
        -DUSE_QT6=ON -DQT_NODES_DEVELOPER_DEFAULTS=OFF -DBUILD_TESTING=OFF
        -DBUILD_EXAMPLES=OFF -DBUILD_DOCS=OFF -DQT_NODES_FORCE_TEST_COLOR=OFF
)
vcpkg_cmake_install()
vcpkg_cmake_config_fixup(PACKAGE_NAME QtNodes CONFIG_PATH lib/cmake/QtNodes)
vcpkg_copy_pdbs()
file(REMOVE_RECURSE "${CURRENT_PACKAGES_DIR}/debug/include" "${CURRENT_PACKAGES_DIR}/debug/share")
vcpkg_install_copyright(FILE_LIST "${SOURCE_PATH}/LICENSE.rst")
