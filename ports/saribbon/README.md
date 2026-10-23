# saribbon 2.8.0

Qt6 共享 SARibbonBar，关闭 FramelessHelper 与 SnapLayout。复用 QtTools 翻译工具；迁入 UTF-8、生成头和配置文件修复。

## 来源与构建

版本、归档 SHA512、补丁及所有构建选项以本目录 `portfile.cmake` 和 `vcpkg.json` 为准。依赖全部通过同一 manifest 安装，不访问旧工程或其他 port 的 buildtrees。

- [czyt1988/SARibbon @ b50d2d5bf0f3](https://github.com/czyt1988/SARibbon/tree/b50d2d5bf0f36caec0df53328f60f6203944ed89)

## 许可与验收

Port 许可表达式：`MIT`。实际分发条件见 [许可说明](../../docs/licensing.md)，本地改动与原因见 [自定义 ports 说明](../../docs/custom-ports.md#saribbon)。

使用根目录 Python 入口构建完整清单，再执行 Release/Debug 验收。消费测试见 [tests](../../tests/CMakeLists.txt)。
