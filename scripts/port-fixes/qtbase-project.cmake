include_guard(GLOBAL)
if(NOT CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    return()
endif()

set(CMAKE_CXX_EXTENSIONS ON)
function(sdk_qtbase_enable_gnu_extensions directory)
    get_property(targets DIRECTORY "${directory}" PROPERTY BUILDSYSTEM_TARGETS)
    foreach(target IN LISTS targets)
        get_target_property(type "${target}" TYPE)
        if(NOT type STREQUAL "INTERFACE_LIBRARY" AND NOT type STREQUAL "UTILITY")
            set_property(TARGET "${target}" PROPERTY CXX_EXTENSIONS ON)
        endif()
    endforeach()
    get_property(subdirectories DIRECTORY "${directory}" PROPERTY SUBDIRECTORIES)
    foreach(subdirectory IN LISTS subdirectories)
        sdk_qtbase_enable_gnu_extensions("${subdirectory}")
    endforeach()
endfunction()

# 通用标准 hook 先设置 C++ 标准与严格模式，再仅为 Qt Base 启用 GNU 扩展。
cmake_language(DEFER DIRECTORY "${CMAKE_SOURCE_DIR}"
    CALL sdk_qtbase_enable_gnu_extensions "${CMAKE_SOURCE_DIR}")
