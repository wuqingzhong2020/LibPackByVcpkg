# scintilla 5.6.7

保持基线 5.6.7 源码，为 Windows/Ubuntu 统一提供 Qt6 ScintillaEditBase 共享控件和 Scintilla::Headers。使用上游 Qt 包装实现，不使用 QScintilla。

文档默认使用 UTF-8，仅接受 `SCI_SETCODEPAGE(SC_CP_UTF8)`。通过 Qt6 原生 UTF-8 转换处理输入、剪贴板和显示，不依赖 Qt5Compat。文件编码转换由应用的读写层负责。

## 来源与构建

版本、归档 SHA512、补丁及所有构建选项以本目录 `portfile.cmake` 和 `vcpkg.json` 为准。依赖全部通过同一 manifest 安装，不访问旧工程或其他 port 的 buildtrees。


## 许可与验收

Port 许可表达式：`HPND`。实际分发条件见 [许可说明](../../docs/licensing.md)，本地改动与原因见 [自定义 ports 说明](../../docs/custom-ports.md#scintilla)。

使用根目录 Python 入口构建完整清单，再执行 Release/Debug 验收。消费测试见 [tests](../../tests/CMakeLists.txt)。
