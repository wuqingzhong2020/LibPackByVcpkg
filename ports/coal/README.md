# coal 3.0.4

共享 Coal，使用公共 Eigen、Boost、Assimp、Octomap 和 Qhull；关闭 Python、ROS 和旧 hpp-fcl 兼容层。补丁只调整依赖查找；JRL CMake 子模块单独固定和校验。

## 来源与构建

版本、归档 SHA512、补丁及所有构建选项以本目录 `portfile.cmake` 和 `vcpkg.json` 为准。依赖全部通过同一 manifest 安装，不访问旧工程或其他 port 的 buildtrees。

- [coal-library/coal @ f0fecd0afeae](https://github.com/coal-library/coal/tree/f0fecd0afeae60a12180516de7bf58106696cdd2)
- [jrl-umi3218/jrl-cmakemodules @ 330567ca8c9b](https://github.com/jrl-umi3218/jrl-cmakemodules/tree/330567ca8c9b342952222a1311a54dbb7ed6608f)

## 许可与验收

Port 许可表达式：`BSD-2-Clause`。实际分发条件见 [许可说明](../../docs/licensing.md)，本地改动与原因见 [自定义 ports 说明](../../docs/custom-ports.md#coal)。

使用根目录 Python 入口构建完整清单，再执行 Release/Debug 验收。消费测试见 [tests](../../tests/CMakeLists.txt)。
