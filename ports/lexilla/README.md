# lexilla 5.4.6

保持基线 5.4.6，构建完整 lexer 集合及支持层。支持层 C++ 类没有稳定 DLL 导出，为供 Scintillua 共用而采用 PIC 静态库；其宽松许可允许此用法，不裁剪为旧支持子集。

## 来源与构建

版本、归档 SHA512、补丁及所有构建选项以本目录 `portfile.cmake` 和 `vcpkg.json` 为准。依赖全部通过同一 manifest 安装，不访问旧工程或其他 port 的 buildtrees。


## 许可与验收

Port 许可表达式：`HPND`。实际分发条件见 [许可说明](../../docs/licensing.md)，本地改动与原因见 [自定义 ports 说明](../../docs/custom-ports.md#lexilla)。

使用根目录 Python 入口构建完整清单，再执行 Release/Debug 验收。消费测试见 [tests](../../tests/CMakeLists.txt)。
