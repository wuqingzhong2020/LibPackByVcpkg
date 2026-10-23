# scintillua 6.7

构建共享 Scintillua，使用外部 Scintilla 头、Lexilla 支持层、Lua 和 LPeg；不内嵌第二套 Lua。lexer 脚本安装到 share/scintillua/lexers，使用方需设置 scintillua.lexers 属性。

## 来源与构建

版本、归档 SHA512、补丁及所有构建选项以本目录 `portfile.cmake` 和 `vcpkg.json` 为准。依赖全部通过同一 manifest 安装，不访问旧工程或其他 port 的 buildtrees。


## 许可与验收

Port 许可表达式：`MIT`。实际分发条件见 [许可说明](../../docs/licensing.md)，本地改动与原因见 [自定义 ports 说明](../../docs/custom-ports.md#scintillua)。

使用根目录 Python 入口构建完整清单，再执行 Release/Debug 验收。消费测试见 [tests](../../tests/CMakeLists.txt)。
