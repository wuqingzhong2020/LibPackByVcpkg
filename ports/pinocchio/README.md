# pinocchio 4.1.0

共享实现库及原生 interface targets，复用 Coal、Eigen、Boost。urdf feature 映射 BUILD_WITH_URDF_SUPPORT，声明 urdfdom 与 urdfdom-headers 依赖；根清单明确启用该 feature。关闭 Python、OpenMP 和可选 AD/SDF 后端，保留模板实例化。

## 来源与构建

版本、归档 SHA512、补丁及所有构建选项以本目录 `portfile.cmake` 和 `vcpkg.json` 为准。依赖全部通过同一 manifest 安装，不访问旧工程或其他 port 的 buildtrees。

- [stack-of-tasks/pinocchio @ 2ae77666e894](https://github.com/stack-of-tasks/pinocchio/tree/2ae77666e894a39127b283dcce3e2399ec19242d)
- [jrl-umi3218/jrl-cmakemodules @ 648efca10ffc](https://github.com/jrl-umi3218/jrl-cmakemodules/tree/648efca10ffc9081c633e5d23d8b069e89eee341)

## 许可与验收

Port 许可表达式：`BSD-2-Clause`。实际分发条件见 [许可说明](../../docs/licensing.md)，本地改动与原因见 [自定义 ports 说明](../../docs/custom-ports.md#pinocchio)。

使用根目录 Python 入口构建完整清单，再执行 Release/Debug 验收。消费测试见 [tests](../../tests/CMakeLists.txt)。
