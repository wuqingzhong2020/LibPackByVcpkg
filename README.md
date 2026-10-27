# C++20 共用第三方 SDK

## 项目背景

这个项目起源于我为公司开发操作六轴机械臂的 CAM 工业软件时，对第三方库的编译与使用记录。这些库最初由我手动编译，后来在公司项目中编写 Python 脚本，把下载、配置和编译等步骤自动化，逐步积累了各个库的构建方式及兼容性处理经验。

本仓库是独立的第三方 SDK 构建项目，使用 vcpkg 清单模式编译和管理依赖。所有清单、自定义 ports、补丁和辅助脚本都在本仓库内；Qt、OpenCV、OCCT 等库共用兼容的底层依赖，并安装到同一套 SDK 中。版本、功能和链接方式以当前清单及 ports 为准。

对于官方 vcpkg 维护的第三方库 port，即使在本项目环境中编译、安装或运行失败，也优先保留官方配方，先考虑通过本仓库的独立兼容脚本或后处理脚本修正。例如 VTK 继续使用官方 port，仅通过 `scripts/port-fixes/` 中的脚本清理 Linux 安装后遗留的空 `bin` 目录。只有脚本无法合理解决问题时，再评估自定义 port；具体处理及原因统一记录在 [ports 与兼容脚本说明](docs/custom-ports.md) 中。

这套依赖也为我个人探索点云文件的逆向建模准备开发环境，涉及 PCL、Qt、OCCT、IfcOpenShell、OpenCV、CGAL 等库，覆盖点云处理、图形界面、几何建模、模型交换与图像处理。选型遵循以下原则：

- **跨平台**：支持 Windows 与 Ubuntu。
- **C++20**：第三方库优先按 C++20 编译并支持 C++20 消费；官方 port 确认不兼容时，按库回退到最高可用标准。
- **商用闭源**：必须保证使用这些第三方库开发的软件，在履行适用许可义务后能够商用并闭源分发。库版本、features、模块范围、链接方式及传递依赖均须满足这一要求，不得引入会要求公开应用自身业务源码的组件。新增、升级依赖或启用 feature 时，必须重新核对最终依赖闭包及实际部署文件的许可。

许可筛选不限于 LGPL；MIT、BSD、Apache、BSL、MPL 等许可下符合商用闭源分发要求的组件，经审核后也可选用。对与该要求不兼容的 GPL/AGPL 等组件，应禁用、替换或通过白名单裁剪。例如，本仓库的自定义 CGAL 仅安装经审核、在履行许可义务后可用于商用闭源软件的模块与头文件子集，明确排除 GPL 模块及直接或间接依赖这些模块的头文件，并逐文件检查许可证与内部 include 依赖；升级或扩充范围时须重新审核白名单。各组件按自身实际适用的许可证履行义务；其中 LGPL、MPL 等许可涉及的库源码、覆盖文件修改、重新链接等要求分别按相应条款处理。具体许可条件及 CGAL 等库的功能限制见 [许可说明](docs/licensing.md) 与 [CGAL port 说明](docs/custom-ports.md#cgal)。

PCL 只启用 `surface-on-nurbs`，保留点云处理和 NURBS 曲面拟合，不启用依赖 VTK 的 `visualization`。OCCT（`opencascade`）启用官方 `vtk` feature，与清单中的独立 VTK 库共用同一安装结果。

Boost 选择官方完整 `boost` 包，入口版本固定为 **1.92.0**，包含 `boost-geometry`、Boost.Python 等官方默认组件，不启用可选 `mpi`。当前固定 baseline 提供同系列 1.92.0 组件；只固定 `boost` 入口不能单独冻结所有传递组件，升级 baseline 时必须一起评估 Boost 组件版本。

OpenCV 关闭 Linux 的 `gtk` 和 Windows 的 `win32ui`，图像显示由应用自己的 Qt 界面负责。图像处理、标定和已启用格式的读写继续保留；当前配置不提供 `cv::imshow()`、`cv::namedWindow()` 等独立窗口功能。

Qt 官方模块不在 `overrides` 中单独指定版本，统一跟随 baseline 和依赖解析。界面统一使用 Qt6，不编译 `qt5compat`。Scintilla 编辑器的文档字节统一使用 UTF-8，支持中文等 Unicode 文本；GBK 等旧编码文件需要由应用在加载时转为 UTF-8，在保存时按需转回原编码。Qt 的 `QString` 仍按 Qt 原生方式使用 UTF-16，与编辑器之间通过 UTF-8 转换。

## C++ 标准与工具链选择

本项目属于探索性质，优先采用最新可用的库版本、编译器和技术，不以生产环境的长期稳定性或与旧项目的源码、二进制兼容为约束，并接受升级带来的适配和重新编译成本。当前使用的具体版本以清单、baseline 和编译配置为准。

当前选择 C++20，是为了在 Windows/MSVC 与 Linux/GCC 两端采用已有稳定 ABI 支持的共同标准基线，同时使用较新的语言和标准库能力。微软已将 `/std:c++20` 列为具有 ABI 兼容性保证的稳定语言模式，见 [MSVC C++20 与语言模式说明](https://devblogs.microsoft.com/cppblog/msvc-cpp20-and-the-std-cpp20-switch/)。GCC 虽然早已实现部分 C++20 特性，但官方明确说明这些特性的 ABI 直到 GCC 16 才稳定；GCC 16 的 libstdc++ 也结束了 C++20 的实验性支持阶段，见 [GCC 标准支持状态](https://gcc.gnu.org/projects/cxx-status.html#cxx20) 与 [GCC 16 发布说明](https://gcc.gnu.org/gcc-16/changes.html)。因此，Linux 开发环境选择 Ubuntu 26.04，并配合显式配置的 GCC 16 工具链。

后续等 MSVC 与 GCC 的正式版本都提供稳定的 C++23 实现及 ABI 支持后，再考虑将项目基线升级到 C++23，并重新验证整套 SDK。按 2026-10-26 核对的官方状态，GCC 的 C++23 支持仍标为实验性；微软已在 MSVC 14.52 候选版中引入 `/std:c++23`，该工具链当时尚未转为正式版，见 [GCC C++23 状态](https://gcc.gnu.org/projects/cxx-status.html#cxx23) 与 [MSVC 14.52 候选版说明](https://devblogs.microsoft.com/cppblog/msvc-build-tools-version-14-52-release-candidate-now-available/)。项目据此继续以 C++20 为基线；配置中的 `cpp23`、`cpp26` 保留用于后续试验。

## 依赖组织与功能范围

同一安装树、同一 triplet 下，同名 port 共用一个版本及所有使用者请求的 feature 并集。`default-features: false` 只控制当前依赖声明，不能关闭其他依赖边请求的功能；新增或升级依赖时先用 `plan` 核对最终集合。

Qt、OpenCV、VTK、OCCT 优先共用 zlib、图像库、FreeType、TBB 等公共依赖；Ceres、Coal、Pinocchio、IfcOpenShell、PCL 等共用 Eigen 与 Boost。CCCoreLib 保留与源码耦合的私有 nanoflann，OpenCV 的内部 FLANN 与 PCL 的外部 FLANN 分别遵循上游接口；具体例外在 ports 说明中维护。

| 库或组合 | 当前功能选择 |
| --- | --- |
| Ceres | 启用 `schur`，不启用 SuiteSparse、METIS、LAPACK、CUDA |
| Qt Base（两端共用） | Widgets/OpenGL 界面、Concurrent、Network/OpenSSL、SQLite；显式启用 `async-io`、`brotli`、`dnslookup`、`icu`、`pcre2`、`sessionmanager`、`testlib`、`zstd`，保留 FreeType、HarfBuzz、JPEG、PNG |
| Qt Base（Windows） | 增加 `windeployqt`，用于收集应用部署依赖 |
| Qt Base（Linux） | `fontconfig` 匹配字体，`xcb` 提供 X11 窗口；`xcb-xlib`、`egl` 分别提供 XCB 的 GLX、EGL 集成路径，`xcb-sm` 接入 X11 会话管理 |
| CCCoreLib | oneTBB 并行、float 标量，关闭 Qt Concurrent 和 CGAL |
| Coal / Pinocchio | Coal 保留 Qhull、Assimp、OctoMap；Pinocchio 保留运动学、动力学、Coal 碰撞和 URDF 建模，使用公共 URDFDOM；两者关闭 Python 绑定 |
| IfcOpenShell | OCCT 几何后端、IFC2X3 / IFC4 / IFC4X3_ADD2、C++ SDK 与 `IfcConvert`，关闭 CGAL 和 Python |
| CGAL | 仅安装经审核、符合商用闭源分发要求的模块与头文件子集，不限于 LGPL；排除 GPL 模块及依赖它们的头文件，范围见 [许可说明](docs/licensing.md) 与 [port 说明](docs/custom-ports.md#cgal) |
| 编辑器与脚本 | Scintilla / Lexilla / Scintillua 共用 Qt6、Lua、LPeg；独立 Tcl/Tk 与 CPython 分别提供运行环境，CPython 不启用 tkinter |

Qt Base 的三处依赖声明均关闭默认 features，按平台合并；`thread`、`future`、`doubleconversion`、`sql` 由依赖关系自动引入。当前不启用 `dbus`、`ioring`、`vulkan`、`sql-psql`、`xrender` 和原生 `wayland`。`dnslookup` 提供 `QDnsLookup` 的专用 DNS 记录查询；`testlib` 提供 Qt Test 库，不代表构建 Qt 自身的全部测试。

Linux 不能只凭 `opengl`、`xcb` 判断 Qt OpenGL 窗口后端完整：固定 Qt 6.11.2 的 XCB/GLX 插件依赖 `xcb-xlib`，XCB/EGL 插件依赖 `egl`。会话保存/恢复需要桌面支持并由应用处理回调；Wayland 桌面依靠 XWayland 运行，增加 `egl` 不会启用原生 Wayland。相关依据见 [Qt 配置源码](https://github.com/qt/qtbase/blob/v6.11.2/src/gui/configure.cmake)。本次 feature 调整已通过 Windows、Ubuntu 的 Release、Debug 构建及消费验证；Linux 的 XCB/GLX、XCB/EGL 配置均已确认启用，Qt 消费程序也已在 WSLg 的 XCB 后端运行通过。该用例未创建 OpenGL 上下文，不代表全部图形驱动或渲染场景已经验证。

Windows 与 Ubuntu 共用源码和清单，分别使用各自的编译器、安装树和运行资源。Qt、VTK 的宿主工具与对应库版本配套；启动 `build.py` 的宿主 Python 独立于 SDK 内的 Python。库的源码获取、依赖排序和编译由 vcpkg 管理，`build.py` 负责读取配置、组织命令及调用验证和许可收集。

## 使用方式

先复制 `config.ini.example` 为 `config.ini`，然后填写自己的编译环境。Windows 读取 `[env_win]`，WSL/Linux 读取 `[env_linux]`。两节放在同一个文件，运行命令时不用手动切换平台。

`config.ini` 保存本机路径，已加入 Git 忽略；仓库提交的是示例文件。新电脑或新 checkout 需要重新复制并填写。脚本只读取所选的本仓库配置。

```powershell
Copy-Item config.ini.example config.ini
```

Linux 对应命令为 `cp config.ini.example config.ini`。已有 `config.ini` 时直接编辑，不必重新复制。

### Windows 配置

```ini
[env_win]
TOOLCHAIN = vc143
CPP_STANDARD = cpp20
VCPKG_ROOT = D:/app/vcpkg/vcpkg
VS_PATH = D:/app/vs/2022/Community
CMAKE_EXE = D:/app/CMake/bin/cmake.exe
CMAKE_GENERATOR = Visual Studio 17 2022
JOBS = 12
BUILD_DIR =
OUTPUT_DIR =
DOWNLOAD_DIR =
BINARY_CACHE_DIR =
```

切换到另一套 MSVC 时，修改 `TOOLCHAIN`、`VS_PATH`、`CMAKE_GENERATOR`，使三者与安装的工具匹配。例如 v145 使用 `vc145` 和对应 VS2026 安装目录、`Visual Studio 18 2026` 生成器，并使用支持该生成器的 CMake。无需新增 Python 配置表、triplet 或 preset。

Windows 消费测试当前使用 Visual Studio 生成器；脚本会把 `VS_PATH` 和 toolset 同时传给 vcpkg 与消费测试。需要安装所选 Visual Studio 的 C++ 工具链、Windows SDK，以及宿主 Python 3.10+、Git、CMake。

### WSL Ubuntu 26.04 配置

```ini
[env_linux]
TOOLCHAIN = gcc16
CPP_STANDARD = cpp20
CPP_STANDARD_OVERRIDES = assimp=cpp17, vtk=cpp17
VCPKG_ROOT = /home/zjgg/app/vcpkg
GCC_EXE = /home/zjgg/app/gcc16.02/bin/gcc-16
GXX_EXE = /home/zjgg/app/gcc16.02/bin/g++-16
CMAKE_EXE = /usr/bin/cmake
CMAKE_GENERATOR = Ninja
LD_LIBRARY_PATH = /home/zjgg/app/gcc16.02/lib64:/home/zjgg/app/gcc16.02/lib
JOBS = 4
BUILD_DIR =
OUTPUT_DIR =
DOWNLOAD_DIR =
BINARY_CACHE_DIR =
```

`GCC_EXE`、`GXX_EXE` 填写实际可执行文件，可以带 `-16` 等后缀；切换 GCC15 时修改这两个路径及 `TOOLCHAIN = gcc15`。脚本不会从目录名猜编译器版本，也不会自动寻找其他 GCC；`TOOLCHAIN` 标签与实际工具版本的一致性由用户负责。`LD_LIBRARY_PATH` 按需填写，用于所选 GCC 的运行库。

WSL 使用 Linux 版 Python、CMake、Ninja 和独立的 Linux vcpkg checkout。vcpkg 路径应填写自己的实际安装位置。还需要常规 Linux 构建工具和各 port 要求的开发包；GUI 消费测试需要可用的显示/OpenGL 环境。

本机 WSL 可用内存约 32 GiB，Pinocchio 的 12 路模板实例化会造成内存压力，示例采用 `JOBS = 4`；可根据实际内存调整，也可通过统一命令的 `--jobs` 临时覆盖。

### Ubuntu 26.04.1 环境准备

先准备配置中指定的 GCC/G++，再安装构建工具及清单所需的系统开发包：

```bash
sudo apt-get update
sudo apt-get install -y git python3 cmake ninja-build make pkg-config curl zip unzip \
    autoconf autoconf-archive automake libtool bison flex nasm gperf patchelf perl libc6-dev linux-libc-dev \
    libxi-dev libxt-dev libxtst-dev libxrandr-dev libxcursor-dev libxinerama-dev libglu1-mesa-dev \
    '^libxcb.*-dev' libx11-xcb-dev libxrender-dev libxkbcommon-dev libxkbcommon-x11-dev \
    libegl-dev libsm-dev libice-dev
```

从官方仓库克隆 Linux 版 vcpkg，切到 `vcpkg-configuration.json` 中的 baseline，执行 `bootstrap-vcpkg.sh -disableMetrics`，再把实际目录填入 `VCPKG_ROOT`。上述列表是基础工具，部分 ports 还需要额外开发包。

源码可通过 `/mnt/d` 与 Windows 共用；四个生成目录留空时，仍在仓库内按编译器与 C++ 标准命名。编译以普通用户运行，系统软件包安装才需要 `sudo`。vcpkg 自行下载的辅助工具保存在 `DOWNLOAD_DIR`，不替换配置中显式指定的编译器。

### 配置项与输出目录

路径可以是绝对路径，也可以相对于本仓库；不要在 INI 路径两端加引号，含空格的路径直接填写即可。编译器和 vcpkg 路径必须填写，不依赖环境变量中的默认选择。`CMAKE_EXE`、`CMAKE_GENERATOR` 用于本项目的消费测试；第三方 ports 的构建方式和辅助工具仍由 vcpkg 管理。

四个目录留空时按 `TOOLCHAIN` 和 `CPP_STANDARD` 命名：

| 用途 | Windows 示例 | Linux 示例 |
| --- | --- | --- |
| `BUILD_DIR`：临时文件、日志、报告 | `build_vc143_cpp20/` | `build_gcc16_cpp20/` |
| `OUTPUT_DIR`：SDK 安装根目录 | `install_vc143_cpp20/` | `install_gcc16_cpp20/` |
| `DOWNLOAD_DIR`：源码归档与工具下载 | `downloads_vc143_cpp20/` | `downloads_gcc16_cpp20/` |
| `BINARY_CACHE_DIR`：默认二进制缓存 | `binary-cache_vc143_cpp20/` | `binary-cache_gcc16_cpp20/` |

也可以显式填写，支持 `${TOOLCHAIN}`、`${CPP_STANDARD}` 两个占位符。例如在 Linux 节中设置：

```ini
BUILD_DIR = /home/zjgg/sdk-work/build_${TOOLCHAIN}_${CPP_STANDARD}
OUTPUT_DIR = thirdParty_${TOOLCHAIN}_${CPP_STANDARD}
DOWNLOAD_DIR = /home/zjgg/sdk-work/downloads_${TOOLCHAIN}_${CPP_STANDARD}
```

这样可以在 Windows 的同一份源码上启动两套原生构建，同时将 Linux 的大量中间文件放到 WSL 文件系统。两平台的临时目录、安装目录和工具下载目录应分别设置；自定义目录名还需要自行加入 `.gitignore`。构建期间保持源码和配置稳定。脚本不自动搬迁、删除或复用旧 `build/installed`。

安装根目录内部保留 vcpkg 标准布局，例如 `install_vc143_cpp20/x64-windows-v143-cpp20/`。vcpkg 数据库在各自安装根目录内，构建树在 `BUILD_DIR/b`、暂存包在 `BUILD_DIR/p`、注册表缓存在 `BUILD_DIR/registries`，不会写进另一平台的工作目录。

`CPP_STANDARD` 支持 `cpp20`、`cpp23`、`cpp26`，决定目录后缀、第三方库首选编译标准和消费测试标准。默认优先使用 C++20：Windows/vc143 传入 `/std:c++20`，Ubuntu/GCC 传入 `-std=c++20`，不依赖编译器默认值。C 库的 C 编译参数不受影响。

Linux 的 Qt Base 单独使用同级别的 GNU 扩展模式（当前为 `-std=gnu++20`）：Qt 6.11.2 的 128 位整数实现要求 libstdc++ 提供扩展类型支持，严格 `-std=c++20` 会触发其编译检查。此修正保留 C++20 和 int128，不属于标准回退，见 [Qt Base 兼容脚本](docs/custom-ports.md#qtbase官方-port)。其他库及消费测试继续按各自标准配置。

CMake ports 同时收到标准配置，并通过公共 [标准脚本](scripts/cmake/cxx-standard.cmake) 在配置结束时把较低的 target 标准提高到所选值，保留上游要求的更高标准。其他构建系统通过 vcpkg 的 C++ flags 接收设置；若上游使用独立编译命令覆盖这些 flags，后续验证时需检查实际命令并单独处理。MSVC 的 `cpp23`/`cpp26` 通用 flags 使用 `/std:c++latest`，CMake 项目仍按指定数值检查工具链支持。

只有确认官方 port 不兼容首选标准时，才在当前平台配置节的 `CPP_STANDARD_OVERRIDES` 中填入它支持的最高较低标准；优先保留官方 port，不为改变标准复制 port。以下为填写格式，已验证的实际例外见下面的回退记录：

```ini
CPP_STANDARD = cpp20
CPP_STANDARD_OVERRIDES = some-port=cpp17, another-port=cpp14
```

Windows 和 Linux 的例外分别配置，只作用于对应 port，不会连带降低其他库或消费测试的标准。构建失败时不会自动降级；先判断是否真是标准兼容问题，再按 C++17、C++14 等顺序验证并记录原因。MSVC 不提供 C++11 模式，Windows 例外最低为 C++14，GCC 可使用 C++11。

### C++ 标准回退记录

无法使用 C++20 编译的库在此记录 port 名称、库版本、受影响的平台与编译器、实际通过的 C++ 标准及回退原因，并同步到对应平台的 `CPP_STANDARD_OVERRIDES`。只有较低标准实际编译通过后才作为已验证的回退；下载、工具或安装检查失败不作为降低标准的理由。

| port / 版本 | 平台与编译器 | 实际编译标准 | C++20 失败原因及验证范围 |
| --- | --- | --- | --- |
| `assimp` 6.0.5 | Windows x64 / vc143（MSVC 19.44） | C++17 | IFC 导入器 `IFCLoader.cpp` 的 `STEP::operator==` 在 C++20 反向比较候选下出现重载歧义（C2666）。保留官方 port，配置 `assimp=cpp17`；Debug、Release 编译及 vcpkg 安装检查均通过。 |
| `assimp` 6.0.5 | Ubuntu 26.04.1 x64 / GCC 16.2.0 | C++17 | 实际 C++20 构建在 `IFCLoader.cpp:355` 的 `UnitsInContext == nullptr` 出现 `operator==` 重载歧义。Linux 单独配置 `assimp=cpp17`，保留官方 port；Debug、Release 编译及严格安装检查均通过。 |
| `vtk` 9.3.0-pv5.12.1#18 | Windows x64 / vc143（MSVC 19.44） | C++17 | 内置 DIY2 的 `chobo/small_vector.hpp` 使用 C++20 已移除的 `std::allocator::reference`、`pointer` 等成员，产生 C2039 等错误。保留官方 port，配置 `vtk=cpp17`；Debug、Release 编译及 vcpkg 安装检查均通过。 |
| `vtk` 9.3.0-pv5.12.1#18 | Ubuntu 26.04.1 x64 / GCC 16.2.0 | C++17 | 定向编译内置 DIY2 的 `small_vector<int, 4>`：C++20 下缺少 allocator 的 `reference`、`const_reference`、`pointer` 等成员，C++17 通过。Linux 单独配置 `vtk=cpp17`，保留官方 port；完整 Debug、Release 构建及严格安装检查均通过。 |

按 port 生成的标准例外文件只计入对应库的构建标识，调整一个例外时重编该库及受影响的依赖者。修改首选标准或公共标准脚本会影响所有相关库。fmt 继续使用 C++20，通过独立脚本关闭额外的模块库；这是构建选项修正，不属于标准回退，见 [ports 与兼容脚本说明](docs/custom-ports.md#fmt官方-port)。ICU 的 Windows Makefile 会追加 C++17，本仓库通过 [逐 port 编译命令修正](docs/custom-ports.md#icu官方-port) 落实 INI 选择的标准，同样保留官方 port。改变工具路径但沿用相同标签时，已有 CMake 消费缓存可能不再适用，建议同时指定新的 `BUILD_DIR`。

## 命令

填写配置后，Windows 在仓库根目录使用下面的命令；WSL 在同一源码目录中把 `python` 换成 `python3`。也可以从其他目录调用 `build.py` 的完整路径，默认仍读取入口所在仓库的 `config.ini`。

```text
python build.py paths
python build.py doctor
python build.py audit-source
python build.py plan
python build.py build --from-source --clean-buildtrees
python build.py verify --config both
python build.py licenses
```

| 命令 | 作用 |
| --- | --- |
| `paths` | 读取当前平台配置并打印输出路径；不创建目录，不调用编译器或 vcpkg |
| `doctor` | 检查配置指向的工具和固定 baseline，输出工具信息并检查源码边界；不试编译 |
| `audit-source` | 检查源码链接、外部工程路径，生成文件 SHA-256 清单；排除两平台的产物与本机配置 |
| `plan` | 调用 vcpkg `install --dry-run` 查看依赖计划；可能下载数据或运行编译器检测，因此不等于完全无编译活动 |
| `build` | 按清单编译并安装 SDK，host 和 target 显式使用同一套原生编译器配置 |
| `verify` | 对已安装 SDK 配置、编译并运行消费测试；默认检查 Release 和 Debug |
| `licenses` | 收集实际已安装包的许可、来源、版本/features、SBOM 与补充材料 |

`doctor` 只作基础检查，不证明工具链或整套依赖可编译。Windows 会检查所填 VS 目录的 C++ 环境入口；Linux 输出所填 GCC/G++ 的版本供核对。固定 baseline 必须存在于指定 vcpkg checkout，脚本不会自动修改外部工具仓库。

日志位于 `BUILD_DIR/logs/`，状态与源码清单位于 `BUILD_DIR/reports/`，许可材料在 `BUILD_DIR/reports/licenses/`，消费工程在 `BUILD_DIR/consumer/`。失败后查看终端中的日志路径；只有本次命令全部完成才写入 `success: true`。

### 按需选择依赖清单

编译环境统一填写在 `config.ini`；要编译哪些库、使用哪些版本由 JSON 清单决定。默认使用完整的 `vcpkg.json`，也可以通过 `--manifest`（简写 `-m`）选择另一份清单，例如只包含 CPython 的 `vcpkg2.json`：

```text
python build.py paths --manifest vcpkg2.json
python build.py plan --manifest vcpkg2.json
python build.py build --manifest vcpkg2.json --from-source
```

该清单用于单独构建和验证自定义 `python3` 3.15.2 自由线程共享库及九个必要公共 C 库；模块范围见 [CPython 配方说明](docs/custom-ports.md#python3)。完整 SDK 使用主清单 `vcpkg.json`，单独验证 CPython 时可选择这份精简清单。

可以复制清单为 `vcpkg.my-sdk.json` 等文件，分别修改 `dependencies`、`features`、`default-features` 和 `overrides`，再通过 `--manifest` 选择。文件须位于仓库内，参数中的相对路径以仓库根目录为基准；各清单共用根目录 `vcpkg-configuration.json` 的 baseline 与本仓库 overlay ports。

同一份 INI 的所有清单、单库选择共用 `BUILD_DIR` 和 `OUTPUT_DIR`，不会自动增加 `single/` 或按清单名分目录。例如 Windows 使用：

```text
build_vc143_cpp20/
install_vc143_cpp20/x64-windows-v143-cpp20/
```

Linux 对应 `build_gcc16_cpp20/`、`install_gcc16_cpp20/`。部分清单在 `BUILD_DIR/manifest/` 生成临时 `vcpkg.json`，同时保留主安装树中已有的其他包及其 features，避免因缩小清单而移除它们。原清单保持不变；同名库在共用 SDK 中只有一个版本，需要并存不同版本时用不同 INI 显式设置输出目录。`licenses` 统计整套已安装 SDK；消费验证范围见下文。

### 增量构建与单库选择

日常验证直接使用 `python build.py build --manifest vcpkg.json --clean-buildtrees`，Ubuntu 用 `python3`。已安装且版本、features、编译配置、port 和依赖 ABI 没变的库会复用；发生变化时由 vcpkg 重建受影响的库。`--from-source` 只禁用二进制缓存，不强制重编已安装且不变的包。

临时检查一个库时也可以直接使用 `--port`，无需另建清单。默认从 `vcpkg.json` 取出该库；若同时传入 `--manifest`，则从所选清单取出。

以 TBB 为例，先查看计划再构建：

```powershell
python build.py plan --port tbb
python build.py build --port tbb --from-source
```

修改配方、补丁或清单中的版本约束后，重复执行 `build --port tbb`，vcpkg 会检查是否需要重新构建。需要无条件重编译目标库时使用：

```text
python build.py build --port tbb --rebuild
```

`--rebuild` 会重新提取已下载的源码归档，不保留对临时解压源码的手工修改；应把修改保存为 port 补丁。它不会自动升级到网上最新版，版本仍由固定 baseline、所选清单约束和 overlays 决定。

`--port` 使用同一主 SDK，保留所选库的 features、平台条件和版本 overrides，并把已安装的其他包加入临时清单。安装仍在 `OUTPUT_DIR/<triplet>/`，构建和日志仍在 `BUILD_DIR/`。已有依赖可以复用，缺少的传递依赖由 vcpkg 安装。

正式全量构建仍以所选清单为最终安装集合；临时添加的库若要长期保留，应加入 `vcpkg.json`。

通常重复 `build` 即可增量更新。只有明确指定 `--rebuild` 时，才移除目标包及依赖它的已安装包，并按预先保留的清单重建；它们需要一起更新以保持 ABI 一致。底层行为见 [vcpkg manifest 安装说明](https://learn.microsoft.com/en-us/vcpkg/commands/install#manifest-mode)。

`build --port NAME` 支持 registry 或本仓库 overlay 中的库；所选清单已有的库沿用清单中的功能选择。所有库都经过 vcpkg 的构建、安装检查，消费测试按以下范围选择。

只查看路径或安装计划，可分别使用 `paths --port tbb`、`plan --port tbb`。旧的 `single/`、`manifests/` 产物不会自动搬入主 SDK；不能手工混合它们的安装记录。

### 消费验证

`verify` 只消费已安装产物，不触发 vcpkg 安装；不与 `--manifest` 组合。默认同时验证 Release、Debug，搬迁后加 `--installed-root PATH` 指定安装根目录。

| 范围 | 命令 | 覆盖内容 |
| --- | --- | --- |
| 完整 SDK | `python build.py verify --config both` | 现有几何、点云、Qt、脚本嵌入与扩展等消费用例 |
| CPython | `python build.py verify --port python3 --config both` | 解释器、C++ 嵌入、自由线程扩展、九个公共 C 库及其实际加载路径、Tk/Readline 禁用检查 |

CPython 用例只依赖 `CPython::Python`，适用于只验证 CPython 的场景。其他 port 暂不支持 `verify --port`；需要运行验证时使用完整消费测试或库自带程序。单库消费工程与报告分别保存在 `BUILD_DIR/consumer-python3/`、`BUILD_DIR/reports/verify-python3.json`。

完整验证中的 `qt_features` 用例检查 Unicode 数字排序、PCRE2、zstd 资源、DNS TXT、Brotli HTTP 解压和 Qt Test。网络用例使用本机服务；Windows 的 DNS API 不支持替代端口，因此测试需占用空闲的回环 UDP 53 端口，其他平台使用临时端口。

### 库版本与升级

`vcpkg.json` 的 `overrides` 固定直接使用的官方库版本，包含配方修订号 `port-version`（省略时为 0）；Qt 官方模块不单独约束版本，随 baseline 和依赖解析；Boost 完整包入口固定为 1.92.0，组件版本与 baseline 配套评估。本地 overlay 的当前版本标在依赖的 `$comment` 中，实际版本和源码由 `ports/<库名>/vcpkg.json` 与 `portfile.cmake` 控制；overlay 不受 registry 版本约束。

更新外部 vcpkg checkout 不会自动修改本仓库的 baseline。评估升级时，先调整 `vcpkg-configuration.json` 中的 baseline，再按需修改所选清单的 `overrides`，运行 `plan --manifest 清单文件` 查看计划；确认后用 `build --manifest 清单文件` 编译。使用默认清单时省略 `--manifest` 即可。保留原 override 即继续使用该固定版本。Qt、Boost 等配套模块应一起评估；未逐项固定的传递依赖仍由 baseline 和依赖约束解析，更新 baseline 时也要检查其变化。参见 [vcpkg 版本规则](https://learn.microsoft.com/en-us/vcpkg/users/versioning#overrides)。

### 可选参数

| 参数 | 用法 |
| --- | --- |
| `-m PATH` / `--manifest PATH` | 选择依赖清单，默认 `vcpkg.json`；共用 INI 指定的构建和安装目录 |
| `--port NAME` | plan/build 选择一个库及其必要依赖并保留其他已安装包；verify 目前支持 `--port python3` 单独验证 CPython |
| `--rebuild` | 仅限 `build --port`，强制重编目标包及依赖它的已安装包 |
| `--jobs N` | 临时覆盖配置中的 `JOBS`，必须大于 0 |
| `--stage native` | 对 plan/build/verify 选择中间阶段；完整安装与验收使用默认 `full` |
| `--from-source` | 对 plan/build 禁用二进制缓存读写；已安装且 ABI 未变的包仍会复用，不是强制全量重编译 |
| `--clean-buildtrees` | 清理已成功 port 的构建树和暂存包，保留安装结果与下载归档 |
| `--config Release\|Debug\|both` | 选择消费测试配置，默认 `both`；不限制第三方库的构建配置 |
| `--installed-root PATH` | 仅用于 verify，指定已有或搬迁后的 SDK 安装根目录 |

在同一安装树切换 `native/full` 阶段可能导致 vcpkg 移除新阶段不需要的包，先查看对应 `plan`。构建中断后修复问题，再运行同一构建命令即可继续。省略 `--from-source` 时启用默认缓存目录；用户显式设置的 `VCPKG_BINARY_SOURCES` 仍按 vcpkg 规则生效。

## 代码阅读入口

各个自定义第三方库改了什么、为什么需要这些改动，集中说明在 [自定义 ports](docs/custom-ports.md)。

日常换编译器、改标准、改输出目录只编辑 `config.ini`。代码流程是：

```text
build.py → scripts/cli.py → scripts/config.py 读取 INI → 执行所选命令
```

| 文件 | 职责 |
| --- | --- |
| `config.ini.example` | 配置项与填写示例 |
| `vcpkg.json` / `vcpkg2.json` | 完整 SDK 与 CPython 单库清单 |
| `vcpkg-configuration.json` | 官方 registry baseline 与本仓库 overlay 注册 |
| `ports/` / `scripts/port-fixes/` | 自定义配方、补丁与官方 port 的局部兼容脚本 |
| `scripts/config.py` | 读取配置、计算目录；在 `BUILD_DIR/triplets/` 生成 vcpkg 配置 |
| `scripts/manifest.py` | 选择清单或单库，保留已有包并生成临时清单；不分叉输出目录 |
| `scripts/cli.py` | 组织 vcpkg/CMake/CTest 参数、设置运行环境、保存日志和报告 |
| `scripts/licenses.py` | 收集已安装包的许可材料 |
| `licenses/` | 补充第三方许可证、版权声明和来源材料 |
| `tests/test_config.py` | 用模拟命令检查配置传递和目录隔离，不启动第三方编译 |

生成的 triplet 来自 INI，例如 `x64-windows-v143-cpp20` 或 `x64-linux-gcc16-cpp20`，不要手工编辑生成文件。仓库不再维护四套固定 triplet、额外的编译器配置表和重复的 `CMakePresets.json`；消费验收统一通过 `verify` 调用。

仅检查脚本的命令为：

```text
python -B -m unittest discover -s tests -p test_config.py -v
```

## SDK 使用与交付

本仓库包含完整构建源码，使用宿主 Python 3.10+、Git、CMake、平台构建工具和指定的 vcpkg checkout。克隆仓库后填写本机 `config.ini` 即可使用。外部 vcpkg checkout 提供工具与官方 registry；项目的补丁和兼容处理保存在本仓库内。

SDK 默认使用动态库，Windows 使用动态 CRT（Release `/MD`、Debug `/MDd`）；少数原生静态依赖逐项审核。Linux 附带的 `libuuid` 归档含 LGPL 代码，不列入可仅按宽松许可直接静态链接到业务程序的白名单，具体范围见 [许可说明](docs/licensing.md#linux-系统接口与构建工具)。Release DLL 和库在 `bin/`、`lib/`，Debug 在 `debug/bin/`、`debug/lib/`；Linux 共享库在对应的 `lib/` 中。部署或搬迁 SDK 时整体保留安装树结构，包括 Qt 插件、Python/Tcl/Tk 脚本、OCCT 资源及 vcpkg 元数据。

新 CMake 项目使用外部 vcpkg 的 `scripts/buildsystems/vcpkg.cmake`，指定相同 triplet、生成的 overlay-triplets 和 `VCPKG_INSTALLED_DIR`，关闭 `VCPKG_MANIFEST_INSTALL` 后通过 `find_package` 和导出 targets 消费 SDK。`tests/` 是使用参考。消费测试负责各配置的 DLL、Qt 插件、Python/Tcl 资源搜索路径；pybind11 连接 Debug Python 的目标还需要定义 `Py_DEBUG`，示例见 [消费测试](tests/native/CMakeLists.txt)。

应用显式选择 C++20，使用 Eigen 时定义 `EIGEN_MPL2_ONLY`。例如：

```cmake
cmake_minimum_required(VERSION 3.25)
project(app LANGUAGES CXX)
find_package(TBB CONFIG REQUIRED)
find_package(Eigen3 CONFIG REQUIRED)
add_executable(app main.cpp)
target_compile_features(app PRIVATE cxx_std_20)
target_compile_definitions(app PRIVATE EIGEN_MPL2_ONLY)
target_link_libraries(app PRIVATE TBB::tbb Eigen3::Eigen)
```

搬迁后的安装根目录应直接包含 triplet 与 `vcpkg/` 子目录，例如：

```text
python build.py verify --installed-root D:/sdk/robot-cam-installed --config both
```

完整清单 `vcpkg.json` 和单库清单 `vcpkg2.json` 均直接选择自定义 `python3` 3.15.2 自由线程 SDK；其版本由本地 port 控制。模块范围与 ABI 见 [ports 说明](docs/custom-ports.md#python3)，产品分发条件见 [许可说明](docs/licensing.md)。

CPython 复用 vcpkg 的九个公共动态库：libffi、mpdecimal、zlib、OpenSSL、SQLite3、zstd、bzip2、liblzma、Expat。保留上游配套的 mimalloc 和 HACL；当前不引入 Tcl/Tk、GNU Readline，禁用 `_tkinter` 与 `readline`。SDK 主清单中的独立 Tcl/Tk 包不因此成为 CPython 的依赖。

已选的 `pybind11` 和官方完整 Boost 中的 `boost-python`、`boost-parameter-python` 使用同一个自定义 `python3` SDK；各平台的编译和运行兼容性分别验证。其他库新增 Python SDK 依赖或绑定时，仍先交由用户判断。Meson、GLib 等构建工具使用宿主 Python 脚本，不因此开启目标库的 Python 绑定。

### 验证范围

完整 SDK 以主清单构建、严格安装检查及现有 Release/Debug 消费验证为准，覆盖代表性的几何、点云、Qt、Python 嵌入与扩展、URDF 建模、编辑器等接口。检查实际链接与运行资源，不能仅凭安装目录存在或 ABI hash 判定通过。

先验证 Windows，再用同一份清单在 Ubuntu 原生构建和运行；一端成功不能代表另一端成功。搬迁后的 SDK 另用 `verify --installed-root` 验证。中文与空格路径、无显示环境和具体业务用例也按实际覆盖范围判断，不由基础消费测试推断全部兼容。

2026-10-27：CPython 3.15.2 已在 Windows x64 / MSVC 19.44 完成 Release、Debug 源码构建、严格安装检查及独立消费验证；两种配置各通过解释器和 C++ 嵌入两项用例，确认九个公共 C 库的加载来源、Expat 2.9.0 上下文与位置接口、扩展加载后的无 GIL 状态及 Tk/Readline 禁用状态。Boost.Python、boost-parameter-python、Boost 汇总包、pybind11 和安装计划中的独立 Tk 包已同步重建；完整 SDK 消费用例两种配置各 27 项通过，包括 pybind11 嵌入与扩展加载。安装后的两种解释器均通过上游 UCRT 检查，重新查看安装计划无需重建，269 个已安装包的许可材料已收集。pip 配置未调整；本轮未构建 Ubuntu，也未重做搬迁验证，Ubuntu 26.04 的 3.15.2 仍仅完成源码与静态检查。独立验证报告为 `BUILD_DIR/reports/verify-python3.json`，完整 SDK 报告为 `BUILD_DIR/reports/verify-full.json`。

2026-10-26：CPython 3.15.0#1 已在 Windows x64 / MSVC 19.44 和 WSL Ubuntu 26.04.1 / GCC 16.2.0 上通过 Release、Debug 源码构建、严格安装检查及独立消费用例。每种配置均通过解释器与 C++ 嵌入测试，确认九个公共库的实际加载来源、自由线程扩展及 Tk/Readline 禁用状态；两平台搬迁到含中文和空格的目录后，也均通过 Release、Debug 消费用例。Ubuntu 安装范围为 CPython、九个 C 库及四个构建辅助包，共 14 包；本记录不代表完整 Ubuntu SDK 已验证。

2026-10-26：Qt 6.11.2 功能调整已在 Windows x64 / MSVC 19.44 完成增量构建与严格安装检查，新增 ICU 78.3#2，重建 12 个受影响的 Qt 及第三方包。ICU Release、Debug 各 519 条 C++ 编译命令均确认使用 C++20；完整 SDK 消费用例在两种配置下各 27 项通过。重新执行安装计划无需重建，269 个已安装包的许可材料已收集。本记录不包含 Ubuntu Qt 构建验证。

2026-10-26：完整 Linux SDK 已在 WSL Ubuntu 26.04.1 x64 / GCC 16.2.0 完成源码构建和严格安装检查，主清单及传递依赖共 278 个 port 全部安装。Release、Debug 消费用例各 27 项通过，另在 WSLg 的 XCB 后端分别运行 Qt 消费程序通过。Assimp、VTK 使用已记录的 C++17 例外，Qt Base 使用 GNU C++20；其余实际记录到的 C++ 编译命令符合所选标准。标准检查共覆盖 78 个包、27,109 条命令。278 个包的许可材料已收集，`libuuid` 静态归档的 LGPL 组成及分发条件见 [许可说明](docs/licensing.md#linux-系统接口与构建工具)。报告位于 `BUILD_DIR/reports/`。

产品交付按实际运行依赖保留所需 DLL/共享库、插件、脚本、资源和许可材料；SDK 中的开发工具不等于应用运行依赖。`licenses` 收集对应安装树的材料，具体分发条件统一见 [许可说明](docs/licensing.md)。
