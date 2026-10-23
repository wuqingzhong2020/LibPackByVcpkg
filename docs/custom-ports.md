# 第三方库 ports 与兼容脚本：改了什么，为什么要改

本仓库优先使用 vcpkg 官方配方。小范围的安装兼容处理放在 `scripts/port-fixes/`，不复制官方 port。`ports/` 只放确需自定义的部分，由根目录 `vcpkg-configuration.json` 注册为 overlay。

以下以固定 baseline `a073c28e52d920cb2465a17512324b3b6684d03a` 为比较对象。目前有 13 个自定义 ports；`at-spi2-core`、`ompl`、`vtk`、`fmt` 均使用官方 port。前三项的兼容处理仅在 Linux 加载，fmt 的选项处理用于两平台。

| Port | 版本 | 保留本地配方的主要原因 |
| --- | --- | --- |
| [cccorelib](#cccorelib) | 2024.04.10 | 补充点云算法库，适配 oneTBB 与共享库安装 |
| [coal](#coal) | 3.0.4 | 补充碰撞检测库，供 Pinocchio 共用 |
| [ifcopenshell](#ifcopenshell) | 0.8.6 | 补充 IFC C++ SDK，处理共享库导出与 OCCT 依赖 |
| [nodeeditor](#nodeeditor) | 3.0.16 | 补充 QtNodes，修复安装后头文件与依赖查找 |
| [pinocchio](#pinocchio) | 4.1.0 | 补充机器人算法库，明确启用 URDF 与 Coal 碰撞功能 |
| [saribbon](#saribbon) | 2.8.0 | 补充 Qt Ribbon 控件，修复编码、生成头与导出配置 |
| [scintillua](#scintillua) | 6.7 | 补充 Lua 着色库，与公共 Lua、LPeg、Lexilla 配套 |
| [tk](#tk) | 9.0.3 | 补充独立 Tk GUI 库，与公共 Tcl 配套 |
| [cgal](#cgal) | 6.2.1 | 按商用闭源要求审核模块与头文件，排除 GPL 模块及依赖它们的头文件 |
| [scintilla](#scintilla) | 5.6.7 | 将原 Win32 构建改为两平台共用的 Qt6 控件构建 |
| [lexilla](#lexilla) | 5.4.6 | 提供跨平台 CMake 包及 Scintillua 需要的支持层 |
| [tcl](#tcl) | 9.0.3 | 为 Linux 上独立构建 Tk 保留配置模板 |
| [python3](#python3) | 3.15.0 | 使用上游原生构建系统，提供自由线程共享 SDK |

每个目录的 `vcpkg.json` 声明版本、依赖和 features；`portfile.cmake` 固定源码、校验值和构建选项；补丁或额外 CMake 文件记录实际差异。具体代码以这些文件为准。

## at-spi2-core（官方 port）

本库最初由 OpenCV 的 `gtk` feature（仅 Linux 系统有效）间接引入，目前项目已不再使用该 feature。

**做了什么：** 直接使用固定 baseline 中的官方 `at-spi2-core` 2.44.1#5，不在 `ports/` 保存配方副本。生成的 Linux triplet 仅在构建这个库时加载兼容脚本：对 Release、Debug 的 `atspi-2.pc` 删除 `-DG_LOG_DOMAIN="dbind"` 的操作补充 `IGNORE_UNCHANGED`，其余调用转交原函数。脚本内容通过 `VCPKG_HASH_ADDITIONAL_FILES` 纳入包的缓存标识；Windows 不加载该脚本。

**为什么：** 当前生成的 `atspi-2.pc` 已不含该宏，官方配方仍要求替换必须产生修改。错误发生在配方执行期间，安装完成后的脚本来不及处理，因此在执行官方配方前安装这一处函数兼容处理。保留严格安装检查，不修改外部 vcpkg 或 registry 缓存；升级 baseline 后可重新评估并移除脚本。

实现：[兼容脚本](../scripts/port-fixes/at-spi2-core.cmake)、[triplet 生成](../scripts/config.py)。默认清单已关闭 OpenCV 的 `gtk`，不再通过该功能引入本库；其他清单需要时仍可使用这段兼容处理。

## fmt（官方 port）

**做了什么：** 保留官方 12.2.0#1 配方，仅为本 port 追加 `FMT_MODULE=OFF`。两平台仍按首选 C++ 标准编译常规 `fmt::fmt` 库；不提供额外的 `import fmt` 模块库。

**为什么：** 上游检测到 C++20 和较新 CMake 时默认启用模块库，Windows 共享构建生成无导出符号的 `fmt-module.dll`，无法通过严格安装检查。本项目使用普通头文件和 `fmt::fmt`，关闭额外模块即可保留 C++20，无需复制 port 或降低标准。脚本仅计入 fmt 的 ABI，严格检查照常执行。

实现：[fmt 选项脚本](../scripts/port-fixes/fmt.cmake)、[triplet 生成](../scripts/config.py)。

## cccorelib

**做了什么：** 增加共享 CCCoreLib 配方，连接同一安装树中的 TBB，关闭 Qt Concurrent 和 CGAL。补丁把旧 TBB 并行代码改为 oneTBB 的 `task_arena`、`parallel_for`，用原子变量保存并行计算状态；补齐 DLL/PDB 安装和 CMake 依赖导出。上游固定版本的 nanoflann 只作为私有构建依赖，不向消费者导出未安装的 nanoflann target，并处理其旧 CMake 策略与 CMake 4 的兼容问题。

**为什么：** 需要在点云距离、八叉树等运算中复用公共 oneTBB，同时让安装后的库能够独立被 `find_package(CCCoreLib)` 使用。仅下载并编译上游源码，不能解决旧 TBB 接口、并发状态及安装导出问题。这里包含并行实现调整，升级时需要检查数值结果与多线程行为。

实现：[配方](../ports/cccorelib/portfile.cmake)、[补丁](../ports/cccorelib/sdk.patch)。

## ompl（官方 port）

**做了什么：** 使用官方 2.0.2 配方，通过 `VCPKG_POST_PORTFILE_INCLUDES` 在配方执行完后清理空 `bin`、`debug/bin`。版本、补丁及构建选项由官方配方维护；官方已关闭 Python 绑定。

**为什么：** Linux 共享库安装到 `lib`，删除附带脚本后留下的空目录会触发严格安装检查。只删除确实为空的目录，非空目录保留。

实现：[空目录清理脚本](../scripts/port-fixes/remove-empty-bin.cmake)。

## vtk（官方 port）

**做了什么：** 使用官方 9.3.0-pv5.12.1#18 配方，共用 OMPL 的空目录清理脚本。当前清单仅启用 `opengl`、`tbb`，没有启用 `python` feature；官方维护其全部源码、补丁和辅助文件。

**为什么：** 工具移到 `tools/vtk` 后可能留下空 `bin` 目录，需在严格安装检查前清理。后处理脚本由 vcpkg 自动计入包的 ABI 标识。

实现：[空目录清理脚本](../scripts/port-fixes/remove-empty-bin.cmake)。

## coal

**做了什么：** 增加共享 Coal 配方，复用 Eigen、Boost、Assimp、Octomap 和 Qhull。补丁使用这些库导出的 CMake CONFIG 包；单独固定 JRL CMake 子模块。关闭 Python、ROS2、日志及旧 hpp-fcl 兼容层。

**为什么：** Pinocchio 的碰撞功能需要 Coal；明确依赖查找方式后，可以与其他库共用同一套几何和模型导入依赖。当前需要 C++ 碰撞 SDK，因此不引入额外 Python/ROS 接口。

实现：[配方](../ports/coal/portfile.cmake)、[补丁](../ports/coal/sdk.patch)。

## ifcopenshell

**做了什么：** 增加共享 C++ SDK 和 `IfcConvert`，使用 OCCT 8.0.1 后端，启用 IFC2X3、IFC4、IFC4X3_ADD2。修复几何内核、schema、序列化器等 Windows DLL 导出，向消费者传递必要宏、头文件路径和依赖；补齐 Boost 的直接依赖，包括只用头文件的组件。导出配置完整加载 OCCT 所需组件，并处理先查找 FoundationClasses 后再查找 IFC 的情况。沿用公共 Eigen 对齐设置，关闭 CGAL、Python 及其他未选后端。

**为什么：** 业务需要通过 C++ 读取 IFC、生成 OCCT 几何，并运行格式转换工具。上游工程能够编译不等于安装后的共享库可以完整链接；缺少导出符号、依赖组件或宏定义都会影响外部消费者。统一 Eigen 和 Boost 设置可保持公共依赖的 ABI 一致。

实现：[配方](../ports/ifcopenshell/portfile.cmake)、[依赖清单](../ports/ifcopenshell/vcpkg.json)、[补丁](../ports/ifcopenshell/sdk.patch)。

## nodeeditor

**做了什么：** 增加基于 Qt6 的共享 QtNodes，关闭示例、测试和文档。补丁补齐公开头文件所需的 include 路径、包版本文件以及对应 Qt 版本的依赖查找；同时修正部分 SVG 路径数据的格式。

**为什么：** 安装后的 QtNodes 应直接供外部项目使用，不要求消费者再手填上游源码中的内部目录。导出包需要找到构建时对应的 Qt，资源文件也需要能被 Qt SVG 正常读取。

实现：[配方](../ports/nodeeditor/portfile.cmake)、[补丁](../ports/nodeeditor/sdk.patch)。

## pinocchio

**做了什么：** 增加共享实现库及上游 interface targets，连接公共 Eigen、Boost、Coal。`urdf` feature 映射到 `BUILD_WITH_URDF_SUPPORT`，并声明 `urdfdom`、`urdfdom-headers`；根清单启用此 feature。保留模板实例化，关闭 Python、OpenMP、SDF、自动微分等未选功能。补丁使单元测试目录遵循 `BUILD_TESTING`，并在 MSVC 下为不可达分支增加 `__assume(0)`，处理 Debug 的 C4716 返回路径错误。

**为什么：** 机器人应用需要从真实 URDF 建模、进行运动学/动力学计算以及碰撞检测，不能只安装无 URDF 的核心头文件。依赖和导出必须与 Coal 共用同一套库；MSVC 的返回路径问题则需要针对性修复。

实现：[配方](../ports/pinocchio/portfile.cmake)、[feature 定义](../ports/pinocchio/vcpkg.json)、[补丁](../ports/pinocchio/sdk.patch)。

## saribbon

**做了什么：** 增加 Qt6 共享 SARibbonBar，关闭 FramelessHelper、SnapLayout、示例和测试。补丁为 MSVC 设置 UTF-8，将生成的版本头放在构建目录，按已有 `.ts` 文件生成翻译而不在构建时改写源码，并在安装包中声明 Qt 依赖；尊重调用方已选择的 C++ 标准。

**为什么：** 避免中文源码受系统代码页影响，减少 Release/Debug 构建对源文件的改写，并让安装后的 Ribbon 控件能通过导出包直接使用。未选窗口扩展不进入当前 SDK 的依赖范围。

实现：[配方](../ports/saribbon/portfile.cmake)、[补丁](../ports/saribbon/sdk.patch)。

## scintilla

**做了什么：** 保持 baseline 的 5.6.7 源码，添加 CMake 包装，编译上游 Qt6 `ScintillaEditBase` 共享控件，安装控件所需头文件，并导出 `Scintilla::ScintillaEditBase` 和 `Scintilla::Headers`。文档统一使用 UTF-8，复用上游 UTF-8 绘制、字符宽度和大小写处理；Qt 文本通过 `QString::fromUtf8()` / `toUtf8()` 转换，移除 `QTextCodec` 和 `qt5compat` 依赖。

**为什么：** baseline 原配方调用 Win32 的 MSBuild 工程；本项目需要 Windows 与 Ubuntu 使用同一套 Qt6 控件接口和 UTF-8 文本格式。新建文档沿用上游的 UTF-8 默认值，拒绝切换到其他代码页；GBK、Big5、Shift-JIS 等旧编码文件由应用在读写时转换。这里使用 Scintilla 自带 Qt 包装，不引入 QScintilla。

实现：[配方](../ports/scintilla/portfile.cmake)、[CMake 包装](../ports/scintilla/CMakeLists.txt)、[UTF-8 补丁](../ports/scintilla/utf8-only.patch)。

## lexilla

**做了什么：** 保持 baseline 的 5.4.6 源码，将 MSBuild 构建改为 CMake，构建完整 lexer 集合和 `lexlib` 支持层，安装相应头文件并导出 `Lexilla::Lexilla`。该库明确使用 PIC 静态库。

**为什么：** Scintillua 需要共用 Lexilla 支持层的 C++ 类，而这些类没有完整的 DLL 导出接口。PIC 静态支持库可以链接进共享 Scintillua，同时保留完整 Lexilla 功能；它是本 SDK 动态库默认策略的一个明确例外。

实现：[配方](../ports/lexilla/portfile.cmake)、[CMake 包装](../ports/lexilla/CMakeLists.txt)。

## scintillua

**做了什么：** 增加共享 Scintillua 的 CMake 构建和安装配置，连接公共 Scintilla 头文件、Lexilla、Lua、LPeg；公开 C API 的定义移到全局作用域，与头文件声明保持一致，内部类和状态保留在匿名命名空间。公开头文件在 Windows 下声明 DLL 导出或导入，并使用与实现一致的 `__stdcall`；Linux 使用默认调用约定和公开符号可见性。安装 lexer 脚本到 `share/scintillua/lexers`，导出 `Scintillua::Scintillua`。

**为什么：** 编辑器需要 Lua lexer 着色能力，并应与其他脚本模块共用 Lua、LPeg。上游头文件面向静态嵌入，DLL 实现的调用约定和匿名命名空间中的定义与公开声明不一致，MSVC C++20 会报告 C2375/C2733；对齐声明和定义后继续使用 C++20。库文件之外还必须提供 lexer 脚本；使用方要将 `scintillua.lexers` 属性指向安装后的脚本目录。

实现：[配方](../ports/scintillua/portfile.cmake)、[CMake 包装](../ports/scintillua/CMakeLists.txt)、[共享库 API 补丁](../ports/scintillua/shared-api.patch)。

## tcl

**做了什么：** 复制固定 baseline 的 Tcl 9.0.3 配方和原生补丁。新增的功能仅在 Unix 安装阶段：将 `tclConfig.sh` 保存为包含 `@TCL_PREFIX@`、`@TCL_SOURCE@` 占位符的模板，放到 `share/tcl`，供 Tk 使用。Windows 构建沿用原生实现。

**为什么：** 原配方会清理这些带构建路径的配置脚本，而独立 Tk 构建又需要它们。模板可以在 Tk 自己的构建目录中填入当次路径，避免 Tk 读取 Tcl 的临时构建树；清理构建树或从二进制缓存恢复 Tcl 后仍有明确的配置输入。该 Linux 路径尚待实际构建验证。

实现：[配方](../ports/tcl/portfile.cmake)，重点看 Unix 分支的模板保存代码。

## tk

**做了什么：** 增加与公共 Tcl 9.0.3 配套的共享 Tk。Windows 使用 NMake，Linux 使用 configure/make；下载固定 Tcl 源码仅用于取得私有头和构建规则，链接已安装的 Tcl。安装脚本、`wish` 和 `Tk::Tk` 配置。Windows 归档构建预先写入固定提交号的 `manifest.uuid`。

**为什么：** 当前需要独立 C/C++ Tk GUI 库，不能用 Python 的 tkinter feature 代替。Tk 依赖 Tcl 私有构建材料，但不应重新构建第二套 Tcl，或读取另一个 port 随时可能被清理的 buildtrees。归档中没有 Git 元数据，预写版本标识可以避免 NMake 失败或误读外层仓库。

实现：[配方](../ports/tk/portfile.cmake)、[导出配置](../ports/tk/TkConfig.cmake)。

## cgal

**做了什么：** 保持 CGAL 6.2.1，增加安装白名单和逐文件检查，当前安装范围为经审核的 46 包、1454 个头文件子集。该范围是固定版本的审核结果，不以 LGPL 作为唯一准入条件。检查各文件实际适用的许可证与内部 include 依赖关系，安装后校验头文件路径清单 SHA256，并检查 `CGAL_LICENSE_ERROR` 开关。GMP、MPFR 和 Boost 使用公共依赖。该包只有头文件，迁移 CMake 配置后清理空 `lib` 目录。

**为什么：** 项目只选用在履行许可义务后允许商用闭源的 CGAL 模块与头文件，许可不限于 LGPL，也可纳入经审核的 BSL、BSD 等内容；GPL 模块及直接或间接依赖这些模块的头文件明确排除。普通全量安装不能表达这个要求。检查需要落实到实际安装内容，避免新增或残留未经选定的头文件。各文件分别按自身许可证分发；更换 CGAL 版本或扩充范围时必须重新核对名单与校验值，不能为通过安装而关闭检查。分发条件见 [许可说明](licensing.md)。

实现：[配方](../ports/cgal/portfile.cmake)、[限制安装补丁](../ports/cgal/restricted-sdk.patch)、[安装后核对](../ports/cgal/verify-inventory.cmake)。

## python3

**做了什么：** 固定上游 `v3.15.0` 及源码校验值。Windows 直接调用 PCbuild/MSBuild，Linux 调用 configure/make；构建 x64、无 GIL 的 Release/Debug 共享库，关闭 JIT、tail-call、pip 和测试模块。保留正常标准库以及 ctypes、decimal、SSL/hashlib、SQLite、zlib、bz2、lzma、zstd、XML 模块。libffi、mpdecimal、zlib、OpenSSL、SQLite3、zstd、bzip2、liblzma、Expat 均由 vcpkg 公共 ports 提供，使用对应 Release/Debug 动态库。保留 CPython 配套的内置 mimalloc 与 HACL。

**为什么：** 需要 CPython 3.15 自由线程接口，同时复用 SDK 已有的公共 C 库。Windows 设置 `KillPython=false`，跳过 PCbuild 的进程清理任务；补丁让扩展链接 vcpkg 导入库，不构建内置 Expat 或下载 CPython externals。Linux 显式传入库路径并限定 pkg-config 到当前配置的 SDK 目录，使用 `--with-system-expat`。安装时处理 DLL 依赖、相对 RUNPATH 与 sysconfig，使解释器和 SDK 可以整体搬迁。

当前明确不引入 Tcl/Tk、GNU Readline：Windows 使用 `IncludeTkinter=false`，Linux 在 `Setup.local` 中禁用 `_tkinter`、`readline`，同时传入 `--without-readline`；也不启用 curses、dbm/gdbm、系统 UUID 后端。此限制针对 CPython，不改变完整 SDK 中独立的 Tcl/Tk 包。内置 mimalloc 涉及自由线程运行时的内部接口，不直接替换为普通公共 mimalloc。

Linux 的 sysconfig 分别计算当前配置前缀和 SDK 公共前缀，移除不可搬迁的构建元数据。保留上游仅在 Release 生成的 `libpython3.so` 转发库，并为这项上游差异设置库数量检查策略；其余严格检查照常执行。

完整清单与单库清单都由本地配方控制版本，不能用 registry override 替代 overlay 的版本声明。

port 沿用官方名称 `python3`，因此官方 pybind11 等库对 `python3` 的依赖也会解析到本地 overlay。消费工程通过 `CPython::Python` 明确选择共享库和自由线程 ABI，pybind11 只提供头文件，不另找系统 Python；单库清单 `vcpkg2.json` 不包含 pybind11。

安装后通过 `find_package(cpython CONFIG REQUIRED)` 和 `CPython::Python` 使用共享库，target 提供自由线程宏和 Debug 宏。Windows 解释器位于 `tools/python3/python.exe`、`tools/python3/debug/python_d.exe`；Linux 对应 `tools/python3/python3.15t`、`tools/python3/debug/python3.15td`。嵌入式宿主应使用 PyConfig 指向对应解释器的标准库目录。

实现：[入口](../ports/python3/portfile.cmake)、[Windows](../ports/python3/windows.cmake)、[Linux](../ports/python3/linux.cmake)、[原有依赖补丁](../ports/python3/external-libraries.patch)、[公共依赖补丁](../ports/python3/public-libraries.patch)。

## 维护这些 ports 时看什么

升级一个库时，先核对配方里的源码提交、归档校验、依赖和选项，再检查补丁是否仍有必要。所有配方、补丁和辅助源码均在本仓库内；补丁来源与具体改动保留在各 port 的源码、版权文件和 Git 历史中。

构建、单库选择和消费验证统一见 [README 命令](../README.md#命令)，各 port 不重复列出操作命令。消费者代码位于 [tests](../tests/CMakeLists.txt)。
