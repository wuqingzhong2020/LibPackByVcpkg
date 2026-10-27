# Qt Base 6.11.2 的 qtypes.cpp 要求 GCC 启用 int128 的标准库支持。
# libstdc++ 在严格 -std=c++NN 下不提供所需 type_traits；仅此 port 使用
# 同级别的 GNU 扩展模式，保留 INI 选择的 C++ 标准，不禁用 int128。
set(SDK_QTBASE_PROJECT_HOOK "${CMAKE_CURRENT_LIST_DIR}/qtbase-project.cmake")
list(APPEND VCPKG_HASH_ADDITIONAL_FILES "${SDK_QTBASE_PROJECT_HOOK}")
list(APPEND VCPKG_CMAKE_CONFIGURE_OPTIONS
    "-DCMAKE_PROJECT_INCLUDE=${SDK_QTBASE_PROJECT_HOOK}")
