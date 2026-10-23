#include <ifcparse/IfcFile.h>
#include <ifcgeom/Iterator.h>
#include <ifcgeom/hybrid_kernel.h>
#include <ifcgeom/Serialization/Serialization.h>
#include <serializers/WavefrontObjSerializer.h>

#include <BRepCheck_Analyzer.hxx>
#include <BRepBndLib.hxx>
#include <BRepGProp.hxx>
#include <BRepPrimAPI_MakeBox.hxx>
#include <GProp_GProps.hxx>
#include <STEPControl_Reader.hxx>

#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>

#ifndef IFC_SHARED_BUILD
#error The SDK must propagate IFC_SHARED_BUILD
#endif
#ifndef IFOPSH_WITH_OPENCASCADE
#error The SDK must propagate its geometry backend
#endif
#ifdef IFOPSH_WITH_CGAL
#error This SDK does not enable CGAL
#endif
// Eigen alignment is inherited from the common compiler/toolchain.
static_assert(__cplusplus >= 202002L);

#ifdef _WIN32
#include <Windows.h>
#define BRIDGE_API __declspec(dllexport)
#else
#define BRIDGE_API __attribute__((visibility("default")))
#endif

namespace {
void require(bool condition, const char* message)
{
    if (!condition) throw std::runtime_error(message);
}

void check_loaded_libraries()
{
#ifdef _WIN32
    for (const char* expected : {EXPECTED_IfcParse, EXPECTED_IfcGeom,
            EXPECTED_geometry_kernel_opencascade, EXPECTED_geometry_serializer,
            EXPECTED_Serializers, EXPECTED_TKernel}) {
        const std::filesystem::path path(expected);
        const HMODULE module = GetModuleHandleW(path.filename().wstring().c_str());
        require(module != nullptr, "Expected SDK DLL was not loaded");
        wchar_t actual[32768] = {};
        require(GetModuleFileNameW(module, actual, 32768) != 0, "Cannot locate loaded DLL");
        require(std::filesystem::equivalent(path, actual), "Loaded DLL comes from another SDK");
        std::cout << "Loaded " << path.generic_string() << '\n';
    }
#endif
}

std::string document(const std::string& schema)
{
    // A 1 x 2 x 3 metre extrusion, declared in millimetres, placed at x=10m.
    return "ISO-10303-21;\nHEADER;\n"
        "FILE_DESCRIPTION(('SDK geometry fixture'),'2;1');\n"
        "FILE_NAME('box.ifc','2026-10-15T00:00:00',('libpack'),('libpack'),'libpack','libpack','');\n"
        "FILE_SCHEMA(('" + schema + "'));\nENDSEC;\nDATA;\n" + R"ifc(
#1=IFCPERSON($,$,'SDK',$,$,$,$,$);
#2=IFCORGANIZATION($,'SDK',$,$,$);
#3=IFCPERSONANDORGANIZATION(#1,#2,$);
#4=IFCAPPLICATION(#2,'1','SDK','SDK');
#5=IFCOWNERHISTORY(#3,#4,$,.ADDED.,$,$,$,0);
#10=IFCCARTESIANPOINT((0.,0.,0.));
#11=IFCAXIS2PLACEMENT3D(#10,$,$);
#12=IFCDIRECTION((0.,0.,1.));
#13=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,0.00001,#11,$);
#14=IFCSIUNIT(*,.LENGTHUNIT.,.MILLI.,.METRE.);
#15=IFCUNITASSIGNMENT((#14));
#16=IFCPROJECT('0xScRe4drECQ4DMSqUjd6d',#5,'SDK',$,$,$,$,(#13),#15);
#20=IFCCARTESIANPOINT((10000.,0.,0.));
#21=IFCAXIS2PLACEMENT3D(#20,$,$);
#22=IFCLOCALPLACEMENT($,#21);
#23=IFCCARTESIANPOINT((0.,0.));
#24=IFCAXIS2PLACEMENT2D(#23,$);
#25=IFCRECTANGLEPROFILEDEF(.AREA.,$,#24,1000.,2000.);
#26=IFCEXTRUDEDAREASOLID(#25,#11,#12,3000.);
#27=IFCSHAPEREPRESENTATION(#13,'Body','SweptSolid',(#26));
#28=IFCPRODUCTDEFINITIONSHAPE($,$,(#27));
#29=IFCBUILDINGELEMENTPROXY('1kTvXnbbzCWw8lcMd1dR4o',#5,'SDK box',$,$,#22,#28,$,$);
ENDSEC;
END-ISO-10303-21;
)ifc";
}

void check_schema(const char* schema)
{
    const auto text = document(schema);
    std::ofstream(std::string(schema) + ".ifc") << text;
    std::istringstream stream(text);
    IfcParse::IfcFile file(stream, static_cast<int>(text.size()));
    require(file.good() && file.instance_by_id(29), "IFC parsing failed");
    namespace geo = ifcopenshell::geometry;
    geo::Settings settings;
    settings.set("iterator-output", geo::settings::NATIVE);
    settings.set("use-world-coords", true);
    auto kernel = geo::kernels::construct(&file, "opencascade", settings);
    IfcGeom::Iterator iterator(std::move(kernel), settings, &file);
    require(iterator.initialize(), "Geometry iterator initialization failed");
    require(std::abs(iterator.unit_magnitude() - 0.001) < 1e-12, "IFC length unit mismatch");
    auto* element = dynamic_cast<IfcGeom::BRepElement*>(iterator.get());
    require(element && element->id() == 29, "Unexpected geometry element");
    std::unique_ptr<IfcGeom::ConversionResultShape> compound(element->geometry().as_compound());
    auto* occ = dynamic_cast<geo::OpenCascadeShape*>(compound.get());
    require(occ && BRepCheck_Analyzer(occ->shape()).IsValid(), "Invalid OCCT shape / RTTI");
    GProp_GProps props;
    BRepGProp::VolumeProperties(occ->shape(), props);
    require(std::abs(props.Mass() - 6.0) < 1e-7, "Extrusion volume is not 6 cubic metres");
    Bnd_Box bounds;
    BRepBndLib::AddOptimal(occ->shape(), bounds, false, false);
    double xmin, ymin, zmin, xmax, ymax, zmax;
    bounds.Get(xmin, ymin, zmin, xmax, ymax, zmax);
    std::cout << schema << " bounds: " << xmin << ',' << ymin << ',' << zmin
        << " -> " << xmax << ',' << ymax << ',' << zmax << '\n';
    require(std::abs(xmin - 9.5) < 1e-5 && std::abs(xmax - 10.5) < 1e-5
        && std::abs(ymin + 1.0) < 1e-5 && std::abs(ymax - 1.0) < 1e-5
        && std::abs(zmin) < 1e-5 && std::abs(zmax - 3.0) < 1e-5, "Placement or unit conversion failed");
    require(!iterator.next() && !iterator.had_error_processing_elements(), "Unexpected IFC geometry count/errors");
    const TopoDS_Shape box = BRepPrimAPI_MakeBox(1., 2., 3.).Shape();
    std::unique_ptr<IfcUtil::IfcBaseClass> triangulated(IfcGeom::tesselate(schema, box, 0.05));
    require(triangulated != nullptr, "Schema geometry serialization failed");
    std::cout << schema << ": one valid solid, volume=6, x=[9.5,10.5], units=mm\n";
}
} // namespace

extern "C" BRIDGE_API int ifcopenshell086_check()
{
    try {
        require(std::string(IFCOPENSHELL_VERSION).find("0.8.6") == 0, "Exported version mismatch");
        for (const char* schema : {"IFC2X3", "IFC4", "IFC4X3_ADD2"}) check_schema(schema);
        ifcopenshell::geometry::Settings geometry;
        ifcopenshell::geometry::SerializerSettings serializer;
        WaveFrontOBJSerializer obj(std::string("serializer.obj"), std::string("serializer.mtl"), geometry, serializer);
        require(obj.ready(), "Serializers DLL is unavailable");
        obj.writeHeader();
        obj.finalize();
        check_loaded_libraries();
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}

extern "C" BRIDGE_API int ifcopenshell086_check_output()
{
    try {
        for (const char* schema : {"IFC2X3", "IFC4", "IFC4X3_ADD2"}) {
            std::ifstream input(std::string(schema) + ".obj");
            unsigned vertices = 0, faces = 0;
            std::string line;
            while (std::getline(input, line)) {
                if (line.rfind("v ", 0) == 0) ++vertices;
                if (line.rfind("f ", 0) == 0) ++faces;
            }
            require(vertices >= 8 && faces >= 12, "IfcConvert produced empty/incomplete OBJ");
        }
        for (const char* name : {"IFC4.stp", "IFC4-original-units.stp"}) {
            STEPControl_Reader reader;
            require(reader.ReadFile(name) == IFSelect_RetDone, "Cannot read converted STEP");
            reader.SetSystemLengthUnit(1.0); // Millimetres per OCCT model unit.
            require(reader.TransferRoots() > 0, "Converted STEP has no roots");
            const TopoDS_Shape shape = reader.OneShape();
            require(!shape.IsNull() && BRepCheck_Analyzer(shape).IsValid(), "Converted STEP is invalid");
            GProp_GProps props;
            BRepGProp::VolumeProperties(shape, props);
            std::cout << name << " roundtrip volume=" << props.Mass() << " mm^3\n";
            require(std::abs(props.Mass() - 6e9) < 1e3, "Converted STEP volume mismatch");
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
