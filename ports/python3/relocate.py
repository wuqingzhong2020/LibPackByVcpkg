"""整理 Linux 安装内容，保留运行资源，将 sysconfig 前缀改为运行时计算。"""
from pathlib import Path
import re
import runpy
import shutil
import sys

destination = Path(sys.argv[1])
prefix, sdk_prefix, work, source = sys.argv[2:]
stdlib = destination / "lib/python3.15t"
# Debug 的库使用独立前缀，但头文件和工具仍引用 SDK 公共前缀。
prefixes = re.compile(f"({re.escape(prefix)}|{re.escape(sdk_prefix)})")
for path in stdlib.glob("_sysconfigdata_*.py"):
    variables = runpy.run_path(str(path))["build_time_vars"]
    lines = ["import os", "_prefix = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))",
             "_sdk_prefix = os.path.dirname(_prefix)" if prefix != sdk_prefix else "_sdk_prefix = _prefix",
             "build_time_vars = {"]
    for key, value in variables.items():
        if isinstance(value, str):
            value = value.replace(work, "").replace(source, "")
            expression = " + ".join(
                "_prefix" if part == prefix else "_sdk_prefix" if part == sdk_prefix else repr(part)
                for part in prefixes.split(value)
            )
        else:
            expression = repr(value)
        lines.append(f"    {key!r}: {expression},")
    path.write_text("\n".join(lines) + "\n}\n", encoding="utf-8")

# 这些目录只用于重建 CPython；SDK 的头文件、扩展和标准库保留。
for pattern in ("**/__pycache__", "config-*", "test"):
    for path in stdlib.glob(pattern):
        if path.is_dir():
            shutil.rmtree(path)
(stdlib / "build-details.json").unlink(missing_ok=True)
# JSON 是同一批构建变量的静态副本；运行时使用上面可搬迁的 Python 配置。
for path in stdlib.glob("_sysconfig_vars_*.json"):
    path.unlink()
