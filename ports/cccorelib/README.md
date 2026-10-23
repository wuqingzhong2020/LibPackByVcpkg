# cccorelib 2024.04.10

共享 CCCoreLib，复用公共 TBB。关闭 Qt Concurrent 和 CGAL；nanoflann 使用上游固定子模块作为私有实现，不导出给消费者。保留迁入的 TBB/导出修复。

## 来源与构建

版本、归档 SHA512、补丁及所有构建选项以本目录 `portfile.cmake` 和 `vcpkg.json` 为准。依赖全部通过同一 manifest 安装，不访问旧工程或其他 port 的 buildtrees。

- [CloudCompare/CCCoreLib @ cac3533c6b9b](https://github.com/CloudCompare/CCCoreLib/tree/cac3533c6b9b773d33122a393533e2a328241d5b)
- [jlblancoc/nanoflann @ 2f54b8eb07c7](https://github.com/jlblancoc/nanoflann/tree/2f54b8eb07c719bc605445e4ec44d61240f5a2ce)

## 许可与验收

Port 许可表达式：`LGPL-2.0-or-later AND MIT AND BSD-2-Clause`。实际分发条件见 [许可说明](../../docs/licensing.md)，本地改动与原因见 [自定义 ports 说明](../../docs/custom-ports.md#cccorelib)。

使用根目录 Python 入口构建完整清单，再执行 Release/Debug 验收。消费测试见 [tests](../../tests/CMakeLists.txt)。
