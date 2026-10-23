#include <sol/sol.hpp>
#include <stdexcept>
extern "C" int luaopen_lpeg(lua_State*);
int main() {
    sol::state lua; lua.open_libraries(sol::lib::base,sol::lib::package,sol::lib::string);
    luaL_requiref(lua.lua_state(),"lpeg",luaopen_lpeg,1); lua_pop(lua.lua_state(),1);
    auto result=lua.safe_script("local p=require('lpeg'); assert(p.match(p.P('hello'),'hello')==6); return 6*7");
    if(!result.valid() || result.get<int>()!=42) throw std::runtime_error("Lua/sol2/LPeg");
}
