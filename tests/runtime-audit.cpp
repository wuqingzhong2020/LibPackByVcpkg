// Check that homonymous DLLs have not been picked up from another SDK on PATH.
// Run at process exit so libraries loaded by the functional test are included.
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <psapi.h>
#include <cstdlib>
#include <cwctype>
#include <filesystem>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
std::wstring lowercase(std::wstring text) {
    for (auto& ch : text) ch = std::towlower(ch);
    return text;
}
void audit() {
    static bool completed = false;
    if (completed) return;
    try {
        const wchar_t* prefix = _wgetenv(L"SDK_EXPECTED_PREFIX");
        const wchar_t* config = _wgetenv(L"SDK_EXPECTED_CONFIG");
        if (!prefix || !config) throw std::runtime_error("SDK runtime audit environment is missing");
        const std::filesystem::path root(prefix);
        std::map<std::wstring, std::filesystem::path> expected;
        std::vector<std::filesystem::path> bins{root / "bin"};
        if (std::wstring(config) == L"Debug") bins.push_back(root / "debug/bin");
        for (const auto& bin : bins) {
            if (!std::filesystem::exists(bin)) continue;
            for (const auto& item : std::filesystem::directory_iterator(bin)) {
                const auto extension = lowercase(item.path().extension().wstring());
                if (extension == L".dll" || extension == L".pyd")
                    expected[lowercase(item.path().filename().wstring())] = item.path();
            }
        }
        std::vector<HMODULE> modules(4096);
        DWORD size = 0;
        if (!K32EnumProcessModules(GetCurrentProcess(), modules.data(),
                                  DWORD(modules.size() * sizeof(HMODULE)), &size) ||
            size > modules.size() * sizeof(HMODULE))
            throw std::runtime_error("Cannot enumerate loaded DLLs");
        unsigned count = 0;
        for (std::size_t i = 0; i < size / sizeof(HMODULE); ++i) {
            wchar_t filename[32768]{};
            if (!GetModuleFileNameW(modules[i], filename, 32768))
                throw std::runtime_error("Cannot locate loaded DLL");
            const std::filesystem::path actual(filename);
            const auto it = expected.find(lowercase(actual.filename().wstring()));
            if (it != expected.end()) {
                if (!std::filesystem::equivalent(it->second, actual)) {
                    std::wcerr << L"Unexpected SDK DLL: " << actual << L"; expected " << it->second << L'\n';
                    std::_Exit(97);
                }
                ++count;
            }
        }
        std::cout << "SDK DLL origin audit: " << count << " shared libraries verified\n";
        std::cout.flush();
        completed = true;
    } catch (const std::exception& error) {
        std::cerr << "SDK DLL audit failed: " << error.what() << '\n';
        std::_Exit(97);
    }
}
const int registered = std::atexit(audit);
}
void sdk_verify_runtime() { audit(); }
#else
void sdk_verify_runtime() {}
#endif
