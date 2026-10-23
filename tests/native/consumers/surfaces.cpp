#include <pcl/surface/on_nurbs/fitting_surface_pdm.h>
#include <pcl/surface/on_nurbs/triangulation.h>
#include <cmath>
#include <stdexcept>
int main() {
    pcl::on_nurbs::NurbsDataSurface data;
    for (int x = 0; x <= 4; ++x)
        for (int y = 0; y <= 4; ++y)
            data.interior.emplace_back(x / 4.0, y / 4.0, 1.0);
    auto initial = pcl::on_nurbs::FittingSurface::initNurbs4Corners(
        3, ON_3dPoint(0,0,1), ON_3dPoint(1,0,1), ON_3dPoint(1,1,1), ON_3dPoint(0,1,1));
    pcl::on_nurbs::FittingSurface fit(&data, initial);
    pcl::on_nurbs::FittingSurface::Parameter parameters;
    parameters.boundary_weight = 0;
    fit.assemble(parameters);
    fit.solve();
    double center[3]{};
    if (!fit.m_nurbs.IsValid() || !fit.m_nurbs.Evaluate(0.5, 0.5, 0, 3, center) ||
        !std::isfinite(center[2]) || std::abs(center[2] - 1.0) > 1e-6)
        throw std::runtime_error("PCL NURBS plane fitting failed");
    pcl::PolygonMesh mesh;
    pcl::on_nurbs::Triangulation::convertSurface2PolygonMesh(fit.m_nurbs, mesh, 8);
    if (mesh.polygons.empty()) throw std::runtime_error("PCL NURBS triangulation failed");
}
