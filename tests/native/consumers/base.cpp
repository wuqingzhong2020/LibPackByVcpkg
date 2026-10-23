#include <assimp/Importer.hpp>
#include <assimp/scene.h>
#include <benchmark/benchmark.h>
#include <tbb/parallel_for.h>
#include <Eigen/Core>
#include <glog/logging.h>
#include <ceres/ceres.h>
#include <zlib.h>
#include <lz4.h>
#include <ft2build.h>
#include FT_FREETYPE_H
#include <gtest/gtest.h>
#include <rapidjson/document.h>
#include <nlohmann/json.hpp>
#include <tinyxml2.h>
#include <atomic>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>

static_assert(__cplusplus >= 202002L);
struct Residual {
    template<class T> bool operator()(const T* x,T* residual) const {
        residual[0]=T(10)-x[0]; return true;
    }
};
TEST(Sdk, CommonDependencies) {
    std::atomic<int> sum{0}; tbb::parallel_for(0, 100, [&](int i) { sum += i; });
    EXPECT_EQ(sum.load(), 4950);
    EXPECT_DOUBLE_EQ((Eigen::Matrix2d::Identity() * Eigen::Vector2d(2, 3)).sum(), 5);
    std::string input(200, 'z'); unsigned char packed[512]; unsigned long size = sizeof(packed);
    ASSERT_EQ(compress(packed, &size, reinterpret_cast<const Bytef*>(input.data()), input.size()), Z_OK);
    char restored[512]; unsigned long restored_size = sizeof(restored);
    ASSERT_EQ(uncompress(reinterpret_cast<Bytef*>(restored), &restored_size, packed, size), Z_OK);
    EXPECT_EQ(std::string(restored, restored_size), input);
    char compressed[512]; int count = LZ4_compress_default(input.data(), compressed, input.size(), sizeof(compressed));
    EXPECT_EQ(LZ4_decompress_safe(compressed, restored, count, sizeof(restored)), 200);
    FT_Library ft{}; ASSERT_EQ(FT_Init_FreeType(&ft), 0); FT_Done_FreeType(ft);
    rapidjson::Document doc; doc.Parse("{\"answer\":42}"); EXPECT_EQ(doc["answer"].GetInt(), 42);
    EXPECT_EQ(nlohmann::json::parse("{\"answer\":42}")["answer"], 42);
    tinyxml2::XMLDocument xml; EXPECT_EQ(xml.Parse("<answer>42</answer>"), tinyxml2::XML_SUCCESS);
    Assimp::Importer importer;
    const char* obj = "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n";
    ASSERT_NE(importer.ReadFileFromMemory(obj, std::strlen(obj), 0, "obj"), nullptr);
    EXPECT_GT(benchmark::CPUInfo::Get().num_cpus, 0);
    double x=0; ceres::Problem problem;
    problem.AddResidualBlock(new ceres::AutoDiffCostFunction<Residual,1,1>(new Residual),nullptr,&x);
    ceres::Solver::Options settings; settings.linear_solver_type=ceres::DENSE_QR;
    ceres::Solver::Summary summary; ceres::Solve(settings,&problem,&summary);
    EXPECT_TRUE(summary.IsSolutionUsable()); EXPECT_NEAR(x,10,1e-6);
    LOG(INFO) << "C++20 common SDK consumer passed";
}
int main(int argc, char** argv) {
    google::InitGoogleLogging(argv[0]); testing::InitGoogleTest(&argc, argv);
    const int result = RUN_ALL_TESTS(); google::ShutdownGoogleLogging(); return result;
}
