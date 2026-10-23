#include <opencv2/opencv.hpp>
#include <pcl/point_types.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl/kdtree/kdtree_flann.h>
#include <nanoflann.hpp>
#include <vtkNew.h>
#include <vtkSphereSource.h>
#include <vtkPolyData.h>
#include <stdexcept>
struct CloudAdapter {
    const pcl::PointCloud<pcl::PointXYZ>& cloud;
    std::size_t kdtree_get_point_count() const { return cloud.size(); }
    float kdtree_get_pt(std::size_t index, std::size_t dimension) const { return cloud[index].data[dimension]; }
    template<class Box> bool kdtree_get_bbox(Box&) const { return false; }
};
int main() {
    cv::Mat input(16,16,CV_8UC3,cv::Scalar(4,8,12)), gray;
    cv::cvtColor(input,gray,cv::COLOR_BGR2GRAY);
    std::vector<unsigned char> encoded; cv::imencode(".png",input,encoded);
    if(cv::norm(cv::imdecode(encoded,cv::IMREAD_COLOR),input)!=0) throw std::runtime_error("PNG round trip");
    auto cloud=std::make_shared<pcl::PointCloud<pcl::PointXYZ>>();
    cloud->push_back({0,0,0}); cloud->push_back({0.01f,0,0}); cloud->push_back({1,0,0});
    pcl::VoxelGrid<pcl::PointXYZ> grid; grid.setInputCloud(cloud); grid.setLeafSize(0.1f,0.1f,0.1f);
    pcl::PointCloud<pcl::PointXYZ> filtered; grid.filter(filtered);
    if(filtered.size()!=2) throw std::runtime_error("PCL filter");
    pcl::KdTreeFLANN<pcl::PointXYZ> tree; tree.setInputCloud(cloud);
    std::vector<int> ids(1); std::vector<float> distances(1);
    if(tree.nearestKSearch(pcl::PointXYZ(1,0,0),1,ids,distances)!=1 || ids[0]!=2) throw std::runtime_error("FLANN search");
    vtkNew<vtkSphereSource> sphere; sphere->Update();
    if(sphere->GetOutput()->GetNumberOfPoints()==0) throw std::runtime_error("VTK mesh");
    CloudAdapter adapter{*cloud};
    using Distance = nanoflann::L2_Simple_Adaptor<float,CloudAdapter>;
    nanoflann::KDTreeSingleIndexAdaptor<Distance,CloudAdapter,3> index(3,adapter,nanoflann::KDTreeSingleIndexAdaptorParams(10));
    index.buildIndex();
    const float query[3]={1,0,0}; decltype(index)::IndexType nearest{}; float squared{};
    if(index.knnSearch(query,1,&nearest,&squared)!=1 || nearest!=2 || squared!=0)
        throw std::runtime_error("nanoflann nearest neighbor");
}
