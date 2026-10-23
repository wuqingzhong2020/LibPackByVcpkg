# 直接调用 PCbuild，所有输出都在此 port 的构建目录中。
# KillPython=false 跳过需要 CodeTaskFactory 的进程清理任务。
set(ENV{PYTHON_FOR_BUILD} "${PYTHON3}")
set(ENV{PYTHONINCLUDE} "${SOURCE_PATH}/Include")
vcpkg_get_windows_sdk(windows_sdk)

foreach(mode IN ITEMS Release Debug)
    string(TOLOWER "${mode}" config)
    if(VCPKG_BUILD_TYPE AND NOT VCPKG_BUILD_TYPE STREQUAL config)
        continue()
    endif()
    set(work "${CURRENT_BUILDTREES_DIR}/${TARGET_TRIPLET}-${config}")
    set(destination "${CURRENT_PACKAGES_DIR}")
    set(dependencies "${CURRENT_INSTALLED_DIR}")
    set(runtime "${CURRENT_PACKAGES_DIR}/tools/${PORT}")
    set(suffix "")
    set(layout_options "")
    set(zlib_name z)
    set(bzip2_name bz2)
    set(expat_name libexpat)
    if(mode STREQUAL "Debug")
        string(APPEND destination "/debug")
        string(APPEND dependencies "/debug")
        string(APPEND runtime "/debug")
        set(suffix "_d")
        set(layout_options --debug)
        set(zlib_name zd)
        set(bzip2_name bz2d)
        set(expat_name libexpatd)
    endif()
    # 使用当前 vcpkg 配置中的导入库，不下载 CPython 的 externals。
    set(ffi "${dependencies}/lib/ffi.lib")
    set(mpdec "${dependencies}/lib/libmpdec.lib")
    set(zlib "${dependencies}/lib/${zlib_name}.lib")
    file(MAKE_DIRECTORY "${work}")
    vcpkg_execute_required_process(
        COMMAND MSBuild.exe "${SOURCE_PATH}/PCbuild/pcbuild.proj"
            /t:Build "/m:${VCPKG_CONCURRENCY}" /nologo /v:minimal
            /p:Platform=x64 "/p:Configuration=${mode}"
            "/p:PlatformToolset=${VCPKG_PLATFORM_TOOLSET}"
            "/p:VCToolsVersion=$ENV{VCToolsVersion}"
            "/p:WindowsTargetPlatformVersion=${windows_sdk}"
            /p:VcpkgEnabled=false /p:VcpkgManifestInstall=false
            /p:DisableGil=true /p:IncludeExternals=false /p:IncludeCTypes=true
            /p:IncludeSSL=true /p:IncludeTkinter=false /p:IncludeTests=false
            /p:KillPython=false /p:UseJIT=false /p:UseTIER2=0 /p:UseTailCallInterp=false
            "/p:PythonForBuild=${PYTHON3}"
            "/p:Py_OutDir=${work}/bin" "/p:Py_IntDir=${work}/obj"
            "/p:ExternalsDir=${work}/unused-externals" /p:zlibNgDir=
            "/p:libffiIncludeDir=${CURRENT_INSTALLED_DIR}/include" "/p:libffiLibrary=${ffi}"
            "/p:mpdecimalIncludeDir=${CURRENT_INSTALLED_DIR}/include" "/p:mpdecimalLibrary=${mpdec}"
            "/p:zlibIncludeDir=${CURRENT_INSTALLED_DIR}/include" "/p:zlibLibrary=${zlib}"
            "/p:VcpkgPythonIncludeDir=${CURRENT_INSTALLED_DIR}/include"
            "/p:bzip2Library=${dependencies}/lib/${bzip2_name}.lib"
            "/p:expatLibrary=${dependencies}/lib/${expat_name}.lib"
            "/p:lzmaLibrary=${dependencies}/lib/lzma.lib"
            "/p:sqlite3Library=${dependencies}/lib/sqlite3.lib"
            "/p:zstdLibrary=${dependencies}/lib/zstd.lib"
            "/p:opensslIncludeDir=${CURRENT_INSTALLED_DIR}/include"
            "/p:opensslOutDir=${dependencies}/lib" /p:SkipCopySSLDLL=true
        WORKING_DIRECTORY "${SOURCE_PATH}/PCbuild"
        LOGNAME "build-${TARGET_TRIPLET}-${config}"
    )
    vcpkg_execute_required_process(
        COMMAND "${PYTHON3}" -B -E "${SOURCE_PATH}/PC/layout"
            -s "${SOURCE_PATH}" --build "${work}/bin/amd64t"
            --copy "${runtime}" --temp "${work}/layout-temp" --arch amd64
            --include-freethreaded --include-alias --include-dev --include-symbols --include-venv
            ${layout_options}
        WORKING_DIRECTORY "${work}"
        LOGNAME "install-${TARGET_TRIPLET}-${config}"
    )
    file(INSTALL "${runtime}/python315t${suffix}.dll" DESTINATION "${destination}/bin")
    file(INSTALL "${runtime}/libs/python315t${suffix}.lib" DESTINATION "${destination}/lib")
    # C++ 宿主从 SDK 的 bin 加载扩展，解释器保留自己的完整运行目录。
    file(GLOB extensions "${runtime}/DLLs/*.pyd")
    file(INSTALL ${extensions} DESTINATION "${destination}/bin")
    if(mode STREQUAL "Release")
        file(INSTALL "${runtime}/include/" DESTINATION "${CURRENT_PACKAGES_DIR}/include/python3.15t")
    endif()
    # 解释器和扩展各自复制运行需要的 DLL，避免依赖开发机 PATH。
    # 末尾斜杠让 vcpkg 将 tools/python3/debug/ 正确识别为 Debug 目录。
    vcpkg_copy_tool_dependencies("${runtime}/")
    vcpkg_copy_tool_dependencies("${runtime}/DLLs")
endforeach()
vcpkg_copy_pdbs()
