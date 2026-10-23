# tcl 9.0.3

复制固定 baseline 的原生 Tcl 9.0.3 配方和补丁。唯一功能改动是 Linux 安装时保存可重定位的 tclConfig 模板供独立 Tk port 使用；Windows 构建沿用原生实现。

## 来源与构建

版本、归档 SHA512、补丁及所有构建选项以本目录 `portfile.cmake` 和 `vcpkg.json` 为准。依赖全部通过同一 manifest 安装，不访问旧工程或其他 port 的 buildtrees。


## 许可与验收

Port 许可表达式：`以安装的原始许可文本为准`。实际分发条件见 [许可说明](../../docs/licensing.md)，本地改动与原因见 [自定义 ports 说明](../../docs/custom-ports.md#tcl)。

使用根目录 Python 入口构建完整清单，再执行 Release/Debug 验收。消费测试见 [tests](../../tests/CMakeLists.txt)。
