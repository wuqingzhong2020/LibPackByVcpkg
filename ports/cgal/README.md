# cgal 6.2.1

仅允许经审核、在履行许可义务后可用于商用闭源软件的模块与头文件，许可不限于 LGPL，也可纳入经审核的 BSL、BSD 等内容；明确排除 GPL 模块及直接或间接依赖这些模块的头文件。当前安装范围为经过许可审查的 46 包、1454 头文件子集，这是固定版本的审核结果。安装前逐文件检查各自适用的许可证与 include 闭合，安装后核对路径清单 SHA256 与 CGAL_LICENSE_ERROR。升级或扩充范围须重新审核，不可为了通过构建取消这些检查。GMP/MPFR 使用公共库。

本包只有头文件。CMake 配置迁移到 `share/CGAL` 后，若 `lib` 目录为空则清理该目录，以通过 vcpkg 的安装布局检查；白名单和头文件清单不受影响。

## 来源与构建

版本、归档 SHA512、补丁及所有构建选项以本目录 `portfile.cmake` 和 `vcpkg.json` 为准。依赖全部通过同一 manifest 安装，不访问旧工程或其他 port 的 buildtrees。

- [CGAL/cgal @ 28811b671a12](https://github.com/CGAL/cgal/tree/28811b671a12b5caa9e3688569dadbc6b3728fe6)

## 许可与验收

Port 许可表达式：`LGPL-3.0-or-later AND BSL-1.0 AND BSD-3-Clause`。该表达式汇总当前包内不同文件适用的许可，不表示每个头文件都同时适用这三种许可，也不是后续模块的准入清单。使用和分发时应分别履行对应文件的许可义务；具体条件见 [许可说明](../../docs/licensing.md)，本地改动与原因见 [自定义 ports 说明](../../docs/custom-ports.md#cgal)。

使用根目录 Python 入口构建完整清单，再执行 Release/Debug 验收。消费测试见 [tests](../../tests/CMakeLists.txt)。
