# 使用 triplet 中明确指定的编译器，而不是 PATH 中的默认 gcc。
vcpkg_cmake_get_vars(compiler_vars)
include("${compiler_vars}")
find_program(MAKE make REQUIRED)
find_program(PKG_CONFIG pkg-config REQUIRED)

foreach(mode IN ITEMS release debug)
    if(VCPKG_BUILD_TYPE AND NOT VCPKG_BUILD_TYPE STREQUAL mode)
        continue()
    endif()
    # 新归档的源码时间戳可能早于旧对象文件，不能跨版本复用 make/DESTDIR 目录。
    set(work "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-${VERSION}-${mode}")
    set(prefix "${CURRENT_INSTALLED_DIR}")
    set(destination "${CURRENT_PACKAGES_DIR}")
    set(runtime "${CURRENT_INSTALLED_DIR}/tools/${PORT}")
    set(options "")
    set(bzip2_name bz2)
    set(runtime_rpath "$$ORIGIN/../../lib")
    if(mode STREQUAL "debug")
        string(APPEND prefix "/debug")
        string(APPEND destination "/debug")
        string(APPEND runtime "/debug")
        set(options --with-pydebug)
        set(bzip2_name bz2d)
        set(runtime_rpath "$$ORIGIN/../../../debug/lib")
    endif()
    file(MAKE_DIRECTORY "${work}/Modules")
    # 不引入 Tcl/Tk、GNU Readline 或其他未声明的系统开发库。
    file(WRITE "${work}/Modules/Setup.local" "*disabled*\n_tkinter\nreadline\n_curses\n_curses_panel\n_dbm\n_gdbm\n_uuid\n")
    string(TOUPPER "${mode}" config)
    set(build_env
        "CC=${VCPKG_DETECTED_CMAKE_C_COMPILER}"
        "CXX=${VCPKG_DETECTED_CMAKE_CXX_COMPILER}"
        "CFLAGS=${VCPKG_DETECTED_CMAKE_C_FLAGS} ${VCPKG_DETECTED_CMAKE_C_FLAGS_${config}}"
        "CPPFLAGS=-I${CURRENT_INSTALLED_DIR}/include"
        "LDFLAGS=-L${prefix}/lib -Wl,-rpath,'${runtime_rpath}:$$ORIGIN/../..:$$ORIGIN'"
        "LIBFFI_CFLAGS=-I${CURRENT_INSTALLED_DIR}/include" "LIBFFI_LIBS=${prefix}/lib/libffi.so"
        "LIBMPDEC_CFLAGS=-I${CURRENT_INSTALLED_DIR}/include" "LIBMPDEC_LIBS=${prefix}/lib/libmpdec.so -lm"
        "ZLIB_CFLAGS=-I${CURRENT_INSTALLED_DIR}/include" "ZLIB_LIBS=${prefix}/lib/libz.so"
        "BZIP2_CFLAGS=-I${CURRENT_INSTALLED_DIR}/include" "BZIP2_LIBS=${prefix}/lib/lib${bzip2_name}.so"
        "LIBLZMA_CFLAGS=-I${CURRENT_INSTALLED_DIR}/include" "LIBLZMA_LIBS=${prefix}/lib/liblzma.so"
        "LIBZSTD_CFLAGS=-I${CURRENT_INSTALLED_DIR}/include" "LIBZSTD_LIBS=${prefix}/lib/libzstd.so"
        "LIBSQLITE3_CFLAGS=-I${CURRENT_INSTALLED_DIR}/include" "LIBSQLITE3_LIBS=${prefix}/lib/libsqlite3.so"
        "LIBEXPAT_CFLAGS=-I${CURRENT_INSTALLED_DIR}/include" "LIBEXPAT_LDFLAGS=${prefix}/lib/libexpat.so"
        "OPENSSL_INCLUDES=-I${CURRENT_INSTALLED_DIR}/include"
        "OPENSSL_LDFLAGS=-L${prefix}/lib" "OPENSSL_LIBS=-lssl -lcrypto"
        "PKG_CONFIG=${PKG_CONFIG}"
        "PKG_CONFIG_LIBDIR=${prefix}/lib/pkgconfig" "PKG_CONFIG_PATH="
        "PYTHON_FOR_REGEN=${PYTHON3}"
        "LD_LIBRARY_PATH=${work}:${prefix}/lib:$ENV{LD_LIBRARY_PATH}"
    )
    vcpkg_execute_required_process(
        COMMAND "${CMAKE_COMMAND}" -E env ${build_env} sh "${SOURCE_PATH}/configure"
            "--prefix=${prefix}" "--bindir=${runtime}"
            --enable-shared --disable-gil --disable-experimental-jit --without-tail-call-interp
            --with-system-libmpdec --without-ensurepip --disable-test-modules --without-readline
            --with-system-expat --with-openssl-rpath=no
            --without-static-libpython --with-suffix= ${options}
        WORKING_DIRECTORY "${work}"
        LOGNAME "configure-${TARGET_TRIPLET}-${mode}"
    )
    vcpkg_execute_required_process(
        COMMAND "${CMAKE_COMMAND}" -E env ${build_env} "${MAKE}" "-j${VCPKG_CONCURRENCY}"
        WORKING_DIRECTORY "${work}"
        LOGNAME "build-${TARGET_TRIPLET}-${mode}"
    )
    vcpkg_execute_required_process(
        COMMAND "${CMAKE_COMMAND}" -E env ${build_env} "${MAKE}" altinstall
            "DESTDIR=${work}/stage" TESTSUBDIRS= "COMPILEALL_OPTS=-j${VCPKG_CONCURRENCY}"
        WORKING_DIRECTORY "${work}"
        LOGNAME "install-${TARGET_TRIPLET}-${mode}"
    )
    # DESTDIR 保留了最终前缀层级，合并到 vcpkg 的暂存包目录。
    file(COPY "${work}/stage${CURRENT_INSTALLED_DIR}/" DESTINATION "${CURRENT_PACKAGES_DIR}")
    if(mode STREQUAL "debug")
        file(COPY_FILE "${destination}/include/python3.15td/pyconfig.h"
            "${CURRENT_PACKAGES_DIR}/include/python3.15t/pyconfig-debug.h")
        file(REMOVE_RECURSE "${destination}/include" "${destination}/share")
    endif()
    # 清除安装时产生的字节码和构建专用文件，并修正 sysconfig 的安装前缀。
    vcpkg_execute_required_process(
        COMMAND "${PYTHON3}" -B "${CURRENT_PORT_DIR}/relocate.py"
            "${destination}" "${prefix}" "${CURRENT_INSTALLED_DIR}" "${work}" "${SOURCE_PATH}"
        WORKING_DIRECTORY "${work}"
        LOGNAME "relocate-${TARGET_TRIPLET}-${mode}"
    )
endforeach()
file(RENAME "${CURRENT_PACKAGES_DIR}/include/python3.15t/pyconfig.h"
    "${CURRENT_PACKAGES_DIR}/include/python3.15t/pyconfig-release.h")
file(WRITE "${CURRENT_PACKAGES_DIR}/include/python3.15t/pyconfig.h"
    "#if defined(Py_DEBUG)\n#include \"pyconfig-debug.h\"\n#else\n#include \"pyconfig-release.h\"\n#endif\n")
vcpkg_fixup_pkgconfig()
file(REMOVE_RECURSE "${CURRENT_PACKAGES_DIR}/share/man")
# 上游只为 Release 生成 libpython3.so 转发库；两种配置的扩展模块相同。
set(VCPKG_POLICY_MISMATCHED_NUMBER_OF_BINARIES enabled)
