# fmt 12.2 在 C++20 下默认额外构建模块库；Windows 生成的模块 DLL 没有导出符号。
# 本 SDK 使用常规 fmt::fmt，关闭额外模块，两平台的普通 fmt 库仍按首选标准编译。
list(APPEND VCPKG_CMAKE_CONFIGURE_OPTIONS "-DFMT_MODULE=OFF")
