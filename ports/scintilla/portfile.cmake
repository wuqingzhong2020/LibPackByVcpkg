vcpkg_check_linkage(ONLY_DYNAMIC_LIBRARY)
vcpkg_download_distfile(ARCHIVE URLS "https://www.scintilla.org/scintilla567.zip" FILENAME "scintilla567.zip"
    SHA512 ad25da6b8781fbb55a2e2904f6331c02817765f8abffdbbfe619890761e609f8490ebbc1261a03d6520846f9496cb65e7fbebbde09c46775959b38a7a02adfaf)
# Keep the upstream Qt control, using its UTF-8 paths without Qt5Compat codecs.
vcpkg_extract_source_archive(SOURCE_PATH ARCHIVE "${ARCHIVE}" PATCHES utf8-only.patch)
file(COPY "${CMAKE_CURRENT_LIST_DIR}/CMakeLists.txt" "${CMAKE_CURRENT_LIST_DIR}/ScintillaConfig.cmake.in" DESTINATION "${SOURCE_PATH}")
vcpkg_cmake_configure(SOURCE_PATH "${SOURCE_PATH}")
vcpkg_cmake_install()
vcpkg_cmake_config_fixup(PACKAGE_NAME Scintilla CONFIG_PATH lib/cmake/Scintilla)
vcpkg_copy_pdbs()
file(REMOVE_RECURSE "${CURRENT_PACKAGES_DIR}/debug/include" "${CURRENT_PACKAGES_DIR}/debug/share")
vcpkg_install_copyright(FILE_LIST "${SOURCE_PATH}/License.txt")
