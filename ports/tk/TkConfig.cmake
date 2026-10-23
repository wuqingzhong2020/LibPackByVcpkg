get_filename_component(_tk_prefix "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
foreach(_component IN ITEMS Tcl Tk)
    if(_component STREQUAL "Tcl")
        set(_names tcl90 tcl9.0)
    else()
        set(_names tcl9tk90 tcl9tk9.0 tk9.0)
    endif()
    find_library(_${_component}_release NAMES ${_names} PATHS "${_tk_prefix}/lib" NO_DEFAULT_PATH REQUIRED NO_CACHE)
    find_library(_${_component}_debug NAMES ${_names} PATHS "${_tk_prefix}/debug/lib" NO_DEFAULT_PATH REQUIRED NO_CACHE)
    if(NOT TARGET Tk::${_component})
        add_library(Tk::${_component} UNKNOWN IMPORTED)
        set_target_properties(Tk::${_component} PROPERTIES
            IMPORTED_CONFIGURATIONS "Release;Debug"
            IMPORTED_LOCATION_RELEASE "${_${_component}_release}"
            IMPORTED_LOCATION_DEBUG "${_${_component}_debug}"
            MAP_IMPORTED_CONFIG_RELWITHDEBINFO Release
            MAP_IMPORTED_CONFIG_MINSIZEREL Release
            INTERFACE_INCLUDE_DIRECTORIES "${_tk_prefix}/include")
    endif()
endforeach()
set_property(TARGET Tk::Tk PROPERTY INTERFACE_LINK_LIBRARIES Tk::Tcl)
set(Tk_VERSION 9.0.3)
set(Tk_FOUND TRUE)
