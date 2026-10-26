# ICU 78.3 的 mh-msys-msvc 在 CXXFLAGS 末尾追加 -std:c++17。
# 保留官方 port，通过 GNU Make 的命令行变量覆盖 C++ 编译命令；继承所有
# CRT、优化、调试与 include 选项，仅去掉已有标准选项并追加 INI 选择的标准。
if(SDK_CXX_STANDARD GREATER 20)
    set(SDK_ICU_CXX_FLAG "-std:c++latest")
else()
    set(SDK_ICU_CXX_FLAG "-std:c++${SDK_CXX_STANDARD}")
endif()
list(APPEND VCPKG_MAKE_OPTIONS
    "'COMPILE.cc=$(CXX) $(CPPFLAGS) $(DEFS) $(filter-out -std:c++% /std:c++%,$(CXXFLAGS)) ${SDK_ICU_CXX_FLAG} -c'")
