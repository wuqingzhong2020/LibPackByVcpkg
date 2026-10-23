# 官方配方在安装过程中清理日志宏，因此必须在执行 portfile 前加载兼容处理。
# triplet 也用于依赖/ABI 探测；此时尚未加载 vcpkg 的构建函数。
if(NOT COMMAND vcpkg_replace_string)
    return()
endif()
include_guard(GLOBAL)

# CMake 将被覆盖的原函数保留为 _vcpkg_replace_string；只覆盖一次。
function(vcpkg_replace_string filename match replace)
    set(options ${ARGN})
    if((filename STREQUAL "${CURRENT_PACKAGES_DIR}/lib/pkgconfig/atspi-2.pc"
        OR filename STREQUAL "${CURRENT_PACKAGES_DIR}/debug/lib/pkgconfig/atspi-2.pc")
        AND match STREQUAL [[-DG_LOG_DOMAIN="dbind"]]
        AND replace STREQUAL ""
        AND NOT "REGEX" IN_LIST options)
        # 宏存在时正常删除，已不存在时允许不修改；其他调用仍使用官方检查。
        list(APPEND options IGNORE_UNCHANGED)
        message(STATUS "at-spi2-core: allow already-clean G_LOG_DOMAIN in ${filename}")
    endif()
    _vcpkg_replace_string("${filename}" "${match}" "${replace}" ${options})
endfunction()
