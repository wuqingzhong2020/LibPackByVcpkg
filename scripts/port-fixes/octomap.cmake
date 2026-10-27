# GCC 16 对 C++20 中已移除的 <ciso646> 发出 #warning。
# OctoMap 1.10.1 仍用它探测标准库，并固定启用 -Werror。
# 上游会覆盖配置级 flags，通过项目 hook 保留 C++20 与原有编译选项。
set(SDK_OCTOMAP_PROJECT_HOOK "${CMAKE_CURRENT_LIST_DIR}/octomap-project.cmake")
list(APPEND VCPKG_HASH_ADDITIONAL_FILES "${SDK_OCTOMAP_PROJECT_HOOK}")
list(APPEND VCPKG_CMAKE_CONFIGURE_OPTIONS
    "-DCMAKE_PROJECT_INCLUDE=${SDK_OCTOMAP_PROJECT_HOOK}")
