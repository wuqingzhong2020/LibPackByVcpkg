# ifcopenshell 0.8.6

共享 C++ SDK 与 IfcConvert，启用 OCCT 后端及 IFC2X3/IFC4/IFC4X3_ADD2。关闭 CGAL/Python 和其他可选后端。补丁保留 DLL/schema 导出与 OCCT 8 适配，去掉旧 Boost/Eigen 精确版本和对齐覆盖。

## 来源与构建

版本、归档 SHA512、补丁及所有构建选项以本目录 `portfile.cmake` 和 `vcpkg.json` 为准。依赖全部通过同一 manifest 安装，不访问旧工程或其他 port 的 buildtrees。

Boost 的直接头文件依赖也在 port 清单中声明，包括 `scope-exit`、`locale`、`property-tree`、`math`、`uuid` 等；不能仅声明参与链接的组件，再依赖其他根库碰巧安装所需头文件。它们使用同一 vcpkg baseline 的 Boost 版本。

- [IfcOpenShell/IfcOpenShell @ ae9f7bfeb652](https://github.com/IfcOpenShell/IfcOpenShell/tree/ae9f7bfeb6525fe1e07ab9a2aa8afb1158127ae2)

## 许可与验收

Port 许可表达式：`LGPL-3.0-or-later`。实际分发条件见 [许可说明](../../docs/licensing.md)，本地改动与原因见 [自定义 ports 说明](../../docs/custom-ports.md#ifcopenshell)。

使用根目录 Python 入口构建完整清单，再执行 Release/Debug 验收。消费测试见 [tests](../../tests/CMakeLists.txt)。

导出配置会完整加载 OCCT 所需组件，并处理上游包对先前 FoundationClasses 查询的整包保护，支持先引入部分 OCCT、再引入 IFC 的消费顺序。
