# tk 9.0.3

Tk 9.0.3 与公共 Tcl 9.0.3 配套。下载固定 Tcl 源码只取得 Tk 构建所需私有头和规则，不再次构建 Tcl。Windows 使用 NMake，Ubuntu 使用 configure/make；安装 Tk::Tk 配置、脚本与 wish。与 Python tkinter feature 无关。

## 来源与构建

版本、归档 SHA512、补丁及所有构建选项以本目录 `portfile.cmake` 和 `vcpkg.json` 为准。依赖全部通过同一 manifest 安装，不访问旧工程或其他 port 的 buildtrees。

- [tcltk/tk @ 72e252081cb8](https://github.com/tcltk/tk/tree/72e252081cb8d1633757b62d7bdbc3d9aa39578e)

## 许可与验收

Port 许可表达式：`TCL`。实际分发条件见 [许可说明](../../docs/licensing.md)，本地改动与原因见 [自定义 ports 说明](../../docs/custom-ports.md#tk)。

使用根目录 Python 入口构建完整清单，再执行 Release/Debug 验收。消费测试见 [tests](../../tests/CMakeLists.txt)。

Windows 归档构建预先生成 `manifest.uuid`，内容使用已固定的 Tk 提交号，避免 NMake 执行 `git rev-parse` 时失败或误读外层仓库。公共 Tcl 的 Windows 标准脚本嵌在 DLL 的 ZIPFS 中，因此不设置不存在的外部 `TCL_LIBRARY` 目录。
