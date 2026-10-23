# nodeeditor 3.0.16

Qt6 共享 QtNodes，关闭示例/测试/文档；复用公共 Qt。迁入补丁修复公开头与导出配置。

## 来源与构建

版本、归档 SHA512、补丁及所有构建选项以本目录 `portfile.cmake` 和 `vcpkg.json` 为准。依赖全部通过同一 manifest 安装，不访问旧工程或其他 port 的 buildtrees。

- [paceholder/nodeeditor @ 7c6341a66a8e](https://github.com/paceholder/nodeeditor/tree/7c6341a66a8e46b8988140b9e60d892b6a3560b3)

## 许可与验收

Port 许可表达式：`BSD-3-Clause`。实际分发条件见 [许可说明](../../docs/licensing.md)，本地改动与原因见 [自定义 ports 说明](../../docs/custom-ports.md#nodeeditor)。

使用根目录 Python 入口构建完整清单，再执行 Release/Debug 验收。消费测试见 [tests](../../tests/CMakeLists.txt)。
