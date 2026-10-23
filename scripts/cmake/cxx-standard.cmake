# 由 triplet 注入官方 CMake port，不修改上游源码。
# 配置结束后再设置 target，防止上游的 CXX_STANDARD 14/17 覆盖 INI 首选值。
include_guard(GLOBAL)

function(sdk_apply_cxx_standard directory)
    get_property(targets DIRECTORY "${directory}" PROPERTY BUILDSYSTEM_TARGETS)
    foreach(target IN LISTS targets)
        get_target_property(type "${target}" TYPE)
        if(type STREQUAL "INTERFACE_LIBRARY" OR type STREQUAL "UTILITY")
            continue()
        endif()
        get_target_property(standard "${target}" CXX_STANDARD)
        # 上游确实要求更高标准时保留；较低标准只能通过 INI 按 port 回退。
        if(NOT standard OR standard LESS SDK_CXX_STANDARD)
            set_property(TARGET "${target}" PROPERTY CXX_STANDARD "${SDK_CXX_STANDARD}")
        endif()
        set_target_properties("${target}" PROPERTIES
            CXX_STANDARD_REQUIRED ON
            CXX_EXTENSIONS OFF)
    endforeach()
    get_property(subdirectories DIRECTORY "${directory}" PROPERTY SUBDIRECTORIES)
    foreach(subdirectory IN LISTS subdirectories)
        sdk_apply_cxx_standard("${subdirectory}")
    endforeach()
endfunction()

cmake_language(DEFER DIRECTORY "${CMAKE_SOURCE_DIR}"
    CALL sdk_apply_cxx_standard "${CMAKE_SOURCE_DIR}")
