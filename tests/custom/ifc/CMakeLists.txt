cmake_minimum_required(VERSION 3.21)
project(ifcopenshell086_consumer LANGUAGES CXX)

find_package(OpenCASCADE 8.0.1 EXACT CONFIG REQUIRED COMPONENTS FoundationClasses)
find_package(IfcOpenShell 0.8.6 EXACT CONFIG REQUIRED)
if(NOT TARGET IfcOpenShell::IfcConvert)
    message(FATAL_ERROR "IfcConvert's installed CMake target is missing")
endif()
set(sdk_ifcconvert "$<TARGET_FILE:IfcOpenShell::IfcConvert>")
if(NOT TARGET TKBRep OR NOT TARGET TKDESTEP)
    message(FATAL_ERROR "IfcOpenShell did not load its OCCT dependencies")
endif()
foreach(name IfcParse IfcGeom geometry_kernel_opencascade geometry_serializer Serializers)
    get_target_property(kind IfcOpenShell::${name} TYPE)
    if(NOT kind STREQUAL "SHARED_LIBRARY")
        message(FATAL_ERROR "${name} is not shared")
    endif()
endforeach()
foreach(schema 2x3 4 4x3_add2)
    foreach(prefix geometry_mapping_ifc geometry_serializer_ifc Serializers_ifc)
        if(TARGET IfcOpenShell::${prefix}${schema})
            message(FATAL_ERROR "Internal schema target leaked into the SDK")
        endif()
    endforeach()
endforeach()

add_library(ifcopenshell086_bridge SHARED bridge.cpp)
target_link_libraries(ifcopenshell086_bridge PRIVATE
    IfcOpenShell::IfcParse IfcOpenShell::IfcGeom
    IfcOpenShell::geometry_kernel_opencascade
    IfcOpenShell::geometry_serializer IfcOpenShell::Serializers)
if(WIN32)
    foreach(name IfcParse IfcGeom geometry_kernel_opencascade geometry_serializer Serializers)
        target_compile_definitions(ifcopenshell086_bridge PRIVATE
            "EXPECTED_${name}=\"$<TARGET_FILE:IfcOpenShell::${name}>\"")
    endforeach()
    target_compile_definitions(ifcopenshell086_bridge PRIVATE
        "EXPECTED_TKernel=\"$<TARGET_FILE:TKernel>\"")
endif()
add_executable(ifcopenshell086_consumer main.cpp)
target_link_libraries(ifcopenshell086_consumer PRIVATE sdk_runtime_audit ifcopenshell086_bridge)

enable_testing()
add_test(NAME sdk_geometry COMMAND ifcopenshell086_consumer)
add_test(NAME converter_version COMMAND "${sdk_ifcconvert}" --version)
# IfcConvert writes UTF-16 on Windows; the C++ test checks its DLL's version.
foreach(schema IFC2X3 IFC4 IFC4X3_ADD2)
    add_test(NAME converter_${schema} COMMAND "${sdk_ifcconvert}"
        --yes --no-progress --fail-on-error
        "${CMAKE_CURRENT_BINARY_DIR}/${schema}.ifc"
        "${CMAKE_CURRENT_BINARY_DIR}/${schema}.obj")
    set_tests_properties(converter_${schema} PROPERTIES DEPENDS sdk_geometry)
endforeach()
add_test(NAME converter_step COMMAND "${sdk_ifcconvert}"
    --yes --no-progress --fail-on-error
    "${CMAKE_CURRENT_BINARY_DIR}/IFC4.ifc" "${CMAKE_CURRENT_BINARY_DIR}/IFC4.stp")
set_tests_properties(converter_step PROPERTIES DEPENDS sdk_geometry)
add_test(NAME converter_step_original_units COMMAND "${sdk_ifcconvert}"
    --yes --no-progress --fail-on-error --convert-back-units
    "${CMAKE_CURRENT_BINARY_DIR}/IFC4.ifc" "${CMAKE_CURRENT_BINARY_DIR}/IFC4-original-units.stp")
set_tests_properties(converter_step_original_units PROPERTIES DEPENDS sdk_geometry)
add_test(NAME converted_geometry COMMAND ifcopenshell086_consumer --check-output)
set_tests_properties(converted_geometry PROPERTIES
    DEPENDS "converter_IFC2X3;converter_IFC4;converter_IFC4X3_ADD2;converter_step;converter_step_original_units")
