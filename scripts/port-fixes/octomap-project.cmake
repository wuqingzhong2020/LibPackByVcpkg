include_guard(GLOBAL)
# 只处理 GCC 的 #warning；其他诊断仍遵循上游的 -Werror。
add_compile_options("$<$<COMPILE_LANG_AND_ID:CXX,GNU>:-Wno-error=cpp>")
