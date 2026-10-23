#include <CCTypes.h>
#include <DgmOctree.h>
#include <DistanceComputationTools.h>
#include <ParallelSort.h>
#include <PointCloud.h>
#include <ReferenceCloud.h>
#include <SimpleMesh.h>
#include <tbb/task_arena.h>

#include <algorithm>
#include <atomic>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <vector>

#ifndef CC_CORE_LIB_USES_TBB
#error The installed CCCoreLib target must propagate its oneTBB ABI definition
#endif
#ifdef CC_CORE_LIB_USES_QT_CONCURRENT
#error This SDK uses oneTBB without QtConcurrent
#endif
static_assert(std::is_same_v<ScalarType, float>);
static_assert(std::is_same_v<PointCoordinateType, float>);

using namespace CCCoreLib;

void require(bool condition, const char* message)
{
    if (!condition)
        throw std::runtime_error(message);
}

void fillCloud(PointCloud& cloud, float height)
{
    require(cloud.reserve(256), "reserve point cloud");
    for (int y = 0; y < 16; ++y)
        for (int x = 0; x < 16; ++x)
            cloud.addPoint(CCVector3(static_cast<float>(x), static_cast<float>(y), height));
    require(cloud.enableScalarField(), "enable scalar field");
}

void checkDistances(const PointCloud& cloud)
{
    for (unsigned i = 0; i < cloud.size(); ++i)
        require(std::abs(cloud.getPointScalarValue(i) - 1.0f) < 1e-5f,
                "expected a distance of one unit");
}

struct CellStats
{
    std::atomic<unsigned> points{0};
    std::atomic<bool> wrongArena{false};
    int threadLimit = 0;
    bool fail = false;
};

bool visitCell(const DgmOctree::octreeCell& cell, void** parameters, NormalizedProgress*)
{
    auto& stats = *static_cast<CellStats*>(parameters[0]);
    stats.points.fetch_add(cell.points->size());
    if (stats.threadLimit > 0 && tbb::this_task_arena::max_concurrency() > stats.threadLimit)
        stats.wrongArena = true;
    return !stats.fail;
}

void testOctree()
{
    PointCloud cloud;
    fillCloud(cloud, 1.0f);
    DgmOctree octree(&cloud);
    require(octree.build() == static_cast<int>(cloud.size()), "build octree");
    for (int limit : {1, 2, 0})
    {
        for (bool adaptive : {false, true})
        {
            CellStats stats;
            stats.threadLimit = limit;
            void* parameters[] = {&stats};
            unsigned cells = adaptive
                ? octree.executeFunctionForAllCellsStartingAtLevel(
                    3, visitCell, parameters, 1, 8, true, nullptr, nullptr, limit)
                : octree.executeFunctionForAllCellsAtLevel(
                    3, visitCell, parameters, true, nullptr, nullptr, limit);
            require(cells > 0 && stats.points == cloud.size(), "visit each point once");
            require(!stats.wrongArena, "oneTBB task_arena must respect the local thread limit");
            stats.fail = true;
            cells = adaptive
                ? octree.executeFunctionForAllCellsStartingAtLevel(
                    3, visitCell, parameters, 1, 8, true, nullptr, nullptr, limit)
                : octree.executeFunctionForAllCellsAtLevel(
                    3, visitCell, parameters, true, nullptr, nullptr, limit);
            require(cells == 0, "propagate a failed parallel cell callback");
        }
    }
}

void testCloudToCloud()
{
    PointCloud reference, compared;
    fillCloud(reference, 0.0f);
    fillCloud(compared, 1.0f);
    for (bool parallel : {false, true})
    {
        DistanceComputationTools::Cloud2CloudDistancesComputationParams parameters;
        parameters.octreeLevel = 4;
        parameters.multiThread = parallel;
        parameters.maxThreadCount = 2;
        require(DistanceComputationTools::computeCloud2CloudDistances(
                    &compared, &reference, parameters) > 0,
                "cloud-to-cloud computation");
        checkDistances(compared);
    }
}

void testCloudToMesh()
{
    PointCloud vertices, compared;
    require(vertices.reserve(3), "reserve vertices");
    vertices.addPoint(CCVector3(-1, -1, 0));
    vertices.addPoint(CCVector3(100, -1, 0));
    vertices.addPoint(CCVector3(-1, 100, 0));
    SimpleMesh mesh(&vertices);
    require(mesh.reserve(1), "reserve triangles");
    mesh.addTriangle(0, 1, 2);
    fillCloud(compared, 1.0f);
    for (bool parallel : {false, true})
    {
        DistanceComputationTools::Cloud2MeshDistancesComputationParams parameters;
        parameters.octreeLevel = 4;
        parameters.multiThread = parallel;
        parameters.maxThreadCount = 2;
        require(DistanceComputationTools::computeCloud2MeshDistances(
                    &compared, &mesh, parameters) == DistanceComputationTools::SUCCESS,
                "cloud-to-mesh computation");
        checkDistances(compared);
    }
}

int main(int argc, char** argv)
{
    try
    {
        require(argc == 2, "specify a test case");
        const std::string test = argv[1];
        if (test == "sort")
        {
            std::vector<int> values{9, -2, 6, 6, 0, 3};
            ParallelSort(values.begin(), values.end());
            require(values == std::vector<int>({-2, 0, 3, 6, 6, 9}), "parallel sort result");
        }
        else if (test == "octree") testOctree();
        else if (test == "cloud_to_cloud") testCloudToCloud();
        else if (test == "cloud_to_mesh") testCloudToMesh();
        else require(false, "unknown test case");
        std::cout << test << " passed\n";
        return 0;
    }
    catch (const std::exception& error)
    {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
