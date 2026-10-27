import sys
sys.path.insert(0, sys.argv[1])
import sdk_extension
assert sdk_extension.answer() == 42
assert sys.version_info[:3] == (3, 15, 2), sys.version
assert not sys._is_gil_enabled()
