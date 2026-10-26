# 商用闭源分发条件

本 SDK 以**履行适用许可义务后允许商用闭源分发**为依赖和模块的筛选标准。LGPL 只是可接受的许可证之一，其他许可下符合条件的组件经审核后也可纳入。实际产品须按分发文件各自适用的许可及链接依赖闭包履行义务，不能仅凭 vcpkg 安装成功或主项目的一条 SPDX 元数据判定。

- MIT/BSD/Apache/BSL/Zlib/Tcl 等：随产品保留适用版权、许可、NOTICE 和要求的归属信息。
- LGPL 库优先共享形式，允许用户替换相容库；提供适用库源码、当地补丁和构建材料，保留许可及修改说明，并满足适用的重新链接、安装信息与逆向调试条款。无需因此公开独立业务代码，但动态链接本身不能免除这些义务。
- Eigen 使用 MPL-2.0 路线；消费者设置 `EIGEN_MPL2_ONLY`。对覆盖文件的修改按 MPL 提供源码。
- CGAL 仅选用经审核、符合上述商用闭源要求的模块与头文件，许可不限于 LGPL；明确排除 GPL 模块，以及直接或间接依赖这些模块的头文件。当前白名单为 46 包、1454 个头文件，这是固定版本的已审核安装范围，后续可在重新审核后扩充。LGPL、BSL、BSD 等文件分别按各自适用的条款履行义务，不将所有 CGAL 头文件统一按 LGPL 处理。保留逐文件许可证及内部依赖闭合检查，不混入白名单外的上游头文件。
- Qt 只使用经确认可走 LGPL 的运行模块；Linguist、Designer 等开发工具及其 GPL 组件单独保留许可。不要把开发工具目录或仅供工具使用的库直接当作闭源应用运行组件。
- Qt 官方分别列出 [SerialPort](https://doc.qt.io/qt-6/qtserialport-index.html#licenses) 与 [SerialBus](https://doc.qt.io/qt-6/qtserialbus-index.html#licenses) 的 LGPLv3 选项；本清单采用该路线。最终以固定 6.11.2 源码中的许可证与实际安装插件为准。
- FreeType 选择 FTL；Paho 在核对原文后选择 EDL；GL2PS 使用其相应许可分支。Qt/VTK/Tcl/Assimp 的第三方代码分别审核。

不启用 Python GNU Readline、OpenCV nonfree/FFmpeg、Qt WebEngine 或 CGAL 白名单之外未经审核的模块与头文件。所有依赖最终以解析后的 feature 并集为准。

## CPython 依赖审核

2026-10-26 核对 CPython 3.15.0 配方、固定版本源码许可及安装树 `share/<port>/copyright`。下列运行库在履行表中条款后均允许商用闭源分发，无需公开独立业务代码；本次没有需要因许可证而移除的公共依赖。

| 运行库 / 版本 | 采用的许可证 | 分发要求或范围 |
| --- | --- | --- |
| libffi 3.8.0 | MIT | 保留版权和许可原文 |
| mpdecimal 4.0.1 | BSD-2-Clause | 二进制随附版权、条件和免责声明 |
| zlib 1.3.2 | Zlib | 不冒称来源；修改源码须标记，源码分发保留声明 |
| OpenSSL 3.6.5 | Apache-2.0 | 随附许可、适用归属及 NOTICE；修改文件标记变更；遵守专利与商标条款 |
| SQLite 3.54.1 | Public Domain | 上游允许商业使用和闭源二进制分发；保留来源记录 |
| zstd 1.5.7 | **BSD-3-Clause 分支** | 双许可中选择 BSD；二进制附版权、条件和免责声明，不借作者名义背书 |
| bzip2 1.0.8 | bzip2-1.0.6 | 保留许可，不冒称来源；修改源码标记，不借作者名义背书 |
| liblzma 5.8.4 | **0BSD，限库本身** | 不启用 `tools`；不引入 XZ 的 GPL 压缩文件辅助脚本；补充许可原文见 `licenses/liblzma/` |
| Expat 2.9.0 | MIT + CC0-1.0 | 保留 MIT 版权许可；同时保留随包 SipHash/CC0 材料 |

CPython 本体按 PSF/Python 历史许可及随包第三方条款分发，保留原始 LICENSE 与修改摘要；它允许闭源修改和分发。保留的 mimalloc 为 MIT，HACL 生成的 C 代码为 MIT，KaRaMeL 支持头带 Apache-2.0/MIT 声明，均不要求公开业务源码。`licenses/python3/` 补充 Apache 2.0 原文及本地变更摘要；原有 port 同时收集 Python LICENSE、HACL 声明和 `Doc/license.rst`（含 mimalloc 条款）。

当前 CPython 禁用 Tcl/Tk 与 GNU Readline。Tcl/Tk 未启用是本项目的范围选择；GNU Readline 无可用的宽松许可分支，故不引入。liblzma 源码归档中的构建脚本或 XZ 辅助工具许可不代表 liblzma 运行库本身的许可；本次只选库，运行用例还会检查实际加载路径。zstd 许可文件保留 GPL 原文不改变本项目已明确选择 BSD 分支的事实。

依据：[CPython 3.15.0 LICENSE](https://github.com/python/cpython/blob/v3.15.0/LICENSE)、[libffi 3.8.0 LICENSE](https://github.com/libffi/libffi/blob/v3.8.0/LICENSE)、[zlib 许可](https://www.zlib.net/zlib_license.html)、[OpenSSL 3.x 许可](https://openssl-library.org/source/license/)、[SQLite 官方说明](https://sqlite.org/copyright.html)、[zstd 1.5.7 LICENSE](https://github.com/facebook/zstd/blob/v1.5.7/LICENSE)、[XZ 5.8.4 组件划分](https://github.com/tukaani-project/xz/blob/v5.8.4/COPYING)、[Expat 2.9.0 COPYING](https://github.com/libexpat/libexpat/blob/R_2_9_0/expat/COPYING)。mpdecimal 与 bzip2 同时核对固定下载归档中的 LICENSE；升级或增加 features 后重新审核。

## Qt Base 功能调整的许可范围

2026-10-26 按固定 baseline 的 Qt 6.11.2 配方核对新增功能，Windows Release、Debug 已完成构建、严格安装检查及消费验证。269 个实际安装包的许可与来源材料已收集到 `BUILD_DIR/reports/licenses/`；具体应用发布时仍须按实际部署文件核对依赖及许可范围。Ubuntu Qt 配置尚未构建验证。

| 组件 | 采用的许可证与范围 |
| --- | --- |
| Brotli 1.2.0 | MIT；保留版权和许可原文，供 Qt Network 的 Brotli 解压功能使用 |
| ICU 78.3 | 根 LICENSE 为 Unicode-3.0，并包含历史 ICU、数据及其他第三方声明；完整保留这些宽松许可材料，不只摘录首段或沿用 port 的简写 `ICU` |
| zstd 1.5.7 | 延续上表的 BSD-3-Clause 分支；Qt 复用公共依赖 |
| Qt Test、会话管理及其他所选 Qt Base 运行功能 | 采用 LGPL-3.0 分支，沿用共享库分发义务并保留内嵌第三方许可；Qt Test 的附属材料已包含在 `licenses/qtbase/` 中 |
| `windeployqt` | 工具源码为 GPL-3.0-only WITH Qt-GPL-exception-1.0；作为开发阶段的部署工具使用，不链接进业务程序、不作为应用运行依赖。单独分发该工具或包含它的 SDK 时，仍须履行工具本身的许可、对应源码等义务 |

Linux 新增的 `egl` port 在该平台包装系统 EGL；X11 的 GLX、会话管理接口依赖系统开发包和运行库。若产品自行打包这些系统库，须按实际实现与版本补齐许可材料。当前不启用 D-Bus、io_uring、Vulkan 或 PostgreSQL 驱动。

依据：[Brotli 1.2.0 LICENSE](https://github.com/google/brotli/blob/v1.2.0/LICENSE)、[ICU 78.3 完整 LICENSE](https://github.com/unicode-org/icu/blob/release-78.3/LICENSE)、[Qt Test 6.11.2 源码许可](https://github.com/qt/qtbase/blob/v6.11.2/src/testlib/qtestcase.cpp)、[windeployqt 6.11.2 源码许可](https://github.com/qt/qtbase/blob/v6.11.2/src/tools/windeployqt/main.cpp)。

## 其他模块与许可材料

已核对固定 Qt 6.11.2 源码：SerialPort、SerialBus 的运行源码及 CAN 插件、SVG、ImageFormats 的相应 Qt 源文件均有 LGPL 分支。SerialBus 的 `src/tools/canbusutil` 则是 GPL-3.0 WITH Qt-GPL-exception；Qt Tools 中 Linguist 和 Designer 的工具实现也包含该分支。原生 `qttools[linguist]` 会引入 `designer` feature，因此开发 SDK 可以保留这些工具，但应用部署不能把整个 `bin` 或 `tools` 目录当成已批准的运行闭包。尤其不要将 Designer 的组件库直接链接进业务程序。验证程序只消费所列运行模块，不使用 Designer 组件；完整源码扫描记录保存在构建报告 `qt-module-source-licenses.json`，第三方内嵌代码仍以随包原文为准。

`python build.py licenses ...` 从实际安装树收集每个 port 的 `copyright` 和可用 SPDX SBOM，并记录哈希、版本和选择说明。它不会把元数据自动转换为“许可已批准”；产品发布前应核对运行依赖与这些材料。源码归档保留在对应编译器的 `downloads_<tag>/`，本仓库 `ports/` 保存补丁和构建方式。

官方 `boost` 总包是只声明依赖的空包，不安装独立许可文件。收集策略明确复用已安装的 `boost-headers/copyright`，保留 `boost` 自身的 SBOM，并继续逐个收集各 Boost 模块的许可；引用的原文缺失时仍会报错。

许可收集成功只表示当前已安装包的材料齐全，报告记录实际包数；完整清单是否安装完成另以 `build-full.json` 为准。

`licenses/qt*/` 保存 Qt 6.11.2 的原始 `qt_attribution.json`、其引用的许可文件和根 `LICENSES`，各模块记录源码 URL 与 SHA512。它们覆盖该源码中的候选第三方组件，包括外部化或未启用的组件；实际使用情况由构建选项与运行闭包确定。收集脚本会核对补充材料的版本，升级对应 port 后须同步更新来源审核。

PCL 原生 port 收集主 LICENSE.txt；启用 `surface-on-nurbs` 时，还应保留 OpenNURBS 的原始说明。本仓库将固定源码中的文本保存到 `licenses/pcl/`，由许可收集命令一并纳入报告；该配置使用公共 ZLIB 和 Eigen 求解器。

Paho C 1.3.16 和 C++ 1.6.0 的固定源码均包含 EDL-1.0 选项，已选择该分支。`licenses/paho-mqtt/` 与 `licenses/paho-mqttpp3/` 保留完整 EDL 及双许可声明，补足原生 port 仅收集 LICENSE/about.html 的情况。

官方依据：[Qt 开源许可义务](https://www.qt.io/licensing/open-source-lgpl-obligations)、[LGPLv3](https://www.gnu.org/licenses/lgpl-3.0.html)、[MPL FAQ](https://www.mozilla.org/en-US/MPL/2.0/FAQ/)、[CGAL 许可](https://www.cgal.org/license.html)。
