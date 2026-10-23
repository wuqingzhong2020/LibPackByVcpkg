#include <tcl.h>
#include <tk.h>
#include <iostream>
void sdk_verify_runtime();
int main(int argc,char** argv) {
    Tcl_FindExecutable(argv[0]); Tcl_Interp* interpreter=Tcl_CreateInterp();
    if(Tcl_Init(interpreter)!=TCL_OK || Tk_Init(interpreter)!=TCL_OK) {
        std::cerr<<Tcl_GetStringResult(interpreter)<<'\n'; return 1;
    }
    int code=Tcl_Eval(interpreter,"package require Tk 9.0; wm withdraw .; label .sdk -text {C++20 SDK}; pack .sdk; update; destroy .");
    if(code!=TCL_OK) std::cerr<<Tcl_GetStringResult(interpreter)<<'\n';
    // Check while Tcl/Tk and the standard output channel are still alive.
    sdk_verify_runtime();
    Tcl_DeleteInterp(interpreter); Tcl_Finalize(); return code==TCL_OK?0:2;
}
