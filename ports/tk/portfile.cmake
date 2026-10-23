vcpkg_check_linkage(ONLY_DYNAMIC_LIBRARY)
vcpkg_from_github(OUT_SOURCE_PATH SOURCE_PATH
    REPO tcltk/tk
    REF 72e252081cb8d1633757b62d7bdbc3d9aa39578e
    SHA512 fadfcb157e5c0756b6c8d870ad914c622537810379b0d26198bd63a129a5e48efc78252acabbbee3c4cc3d2395f88167a3c416500a4c168966985ea484ff3fd1)
# The archive has no Git metadata. Otherwise upstream tries `git rev-parse`
# during NMake and can fail or accidentally identify the enclosing repository.
file(WRITE "${SOURCE_PATH}/manifest.uuid" "git-72e252081cb8d1633757b62d7bdbc3d9aa39578e\n")
# Tk requires Tcl's private headers. Never read another port's buildtrees.
vcpkg_download_distfile(TCL_ARCHIVE
    URLS "https://sourceforge.net/projects/tcl/files/Tcl/9.0.3/tcl9.0.3-src.tar.gz/download"
    FILENAME tcl9.0.3-src.tar.gz
    SHA512 a899333fd96f139d92ad74ee42cc402428677ab2cab8ed3eb1e6e7cb35c7ca7d39aac89b7755b2fb1786512c857c79486d71f49a7821470f669fb9e544dba532)
vcpkg_extract_source_archive(TCL_SOURCE ARCHIVE "${TCL_ARCHIVE}")
if(VCPKG_TARGET_IS_WINDOWS)
    cmake_path(NATIVE_PATH TCL_SOURCE TCL_NATIVE)
    cmake_path(NATIVE_PATH CURRENT_INSTALLED_DIR PREFIX_NATIVE)
    cmake_path(NATIVE_PATH CURRENT_HOST_INSTALLED_DIR HOST_NATIVE)
    vcpkg_add_to_path("${CURRENT_HOST_INSTALLED_DIR}/bin")
    vcpkg_add_to_path("${CURRENT_HOST_INSTALLED_DIR}/tools/tcl/bin")
    vcpkg_install_nmake(SOURCE_PATH "${SOURCE_PATH}" PROJECT_SUBPATH win CL_LANGUAGE C
        OPTIONS
            "TCLDIR=${TCL_NATIVE}" STATS=none CHECKS=none
            "TCLSH=${HOST_NATIVE}\\tools\\tcl\\bin\\tclsh90.exe"
            "TCLSH_NATIVE=${HOST_NATIVE}\\tools\\tcl\\bin\\tclsh90.exe"
        OPTIONS_RELEASE OPTS=pdbs,msvcrt,noembed
            "TCLIMPLIB=${PREFIX_NATIVE}\\lib\\tcl90.lib"
            "TCLSTUBLIB=${PREFIX_NATIVE}\\lib\\tclstub.lib"
        OPTIONS_DEBUG OPTS=pdbs,msvcrt,noembed,symbols
            "TCLIMPLIB=${PREFIX_NATIVE}\\debug\\lib\\tcl90.lib"
            "TCLSTUBLIB=${PREFIX_NATIVE}\\debug\\lib\\tclstub.lib")
    vcpkg_copy_tools(TOOL_NAMES wish90 AUTO_CLEAN)
else()
    message(STATUS "Tk requires system X11 development libraries on Ubuntu (see README)")
    foreach(mode IN ITEMS release debug)
        set(TCL_PREFIX "${CURRENT_INSTALLED_DIR}")
        if(mode STREQUAL "debug")
            string(APPEND TCL_PREFIX "/debug")
        endif()
        file(MAKE_DIRECTORY "${CURRENT_BUILDTREES_DIR}/tcl-${mode}")
        configure_file("${CURRENT_INSTALLED_DIR}/share/tcl/tclConfig-${mode}.sh.in"
            "${CURRENT_BUILDTREES_DIR}/tcl-${mode}/tclConfig.sh" @ONLY)
    endforeach()
    vcpkg_make_configure(SOURCE_PATH "${SOURCE_PATH}/unix"
        DEFAULT_OPTIONS_EXCLUDE "^--(disable|enable)-static"
        OPTIONS --enable-threads --enable-shared
        OPTIONS_RELEASE "--with-tcl=${CURRENT_BUILDTREES_DIR}/tcl-release"
        OPTIONS_DEBUG "--with-tcl=${CURRENT_BUILDTREES_DIR}/tcl-debug")
    vcpkg_make_install()
    vcpkg_fixup_pkgconfig()
    vcpkg_copy_tools(TOOL_NAMES wish9.0 AUTO_CLEAN)
endif()
vcpkg_copy_pdbs()
file(REMOVE_RECURSE "${CURRENT_PACKAGES_DIR}/debug/include" "${CURRENT_PACKAGES_DIR}/debug/share" "${CURRENT_PACKAGES_DIR}/share/man")
file(GLOB configs "${CURRENT_PACKAGES_DIR}/lib/*Config.sh" "${CURRENT_PACKAGES_DIR}/debug/lib/*Config.sh")
if(configs)
    file(REMOVE ${configs})
endif()
file(INSTALL "${CMAKE_CURRENT_LIST_DIR}/TkConfig.cmake" DESTINATION "${CURRENT_PACKAGES_DIR}/share/tk")
vcpkg_install_copyright(FILE_LIST "${SOURCE_PATH}/license.terms" "${TCL_SOURCE}/license.terms")
