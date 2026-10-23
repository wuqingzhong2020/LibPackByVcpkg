#include <clipper2/clipper.h>
#include <libqhull_r/qhull_ra.h>
#include <octomap/OcTree.h>
#include <ompl/base/spaces/RealVectorStateSpace.h>
#include <ompl/geometric/SimpleSetup.h>
#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepGProp.hxx>
#include <GProp_GProps.hxx>
#include <cmath>
#include <cstdio>
#include <stdexcept>
void require(bool ok) { if (!ok) throw std::runtime_error("geometry result mismatch"); }
int main() {
    using namespace Clipper2Lib;
    Paths64 a{{{0,0},{10,0},{10,10},{0,10}}}, b{{{5,0},{15,0},{15,10},{5,10}}};
    require(std::abs(Area(Intersect(a,b,FillRule::NonZero))) == 50);
    octomap::OcTree tree(0.1); tree.updateNode(octomap::point3d(0,0,0), true);
    require(tree.isNodeOccupied(tree.search(0,0,0)));
    auto space = std::make_shared<ompl::base::RealVectorStateSpace>(2);
    ompl::base::RealVectorBounds bounds(2); bounds.setLow(0); bounds.setHigh(1); space->setBounds(bounds);
    ompl::geometric::SimpleSetup setup(space); setup.setStateValidityChecker([](const ompl::base::State*) { return true; });
    ompl::base::ScopedState<> start(space), goal(space); start[0]=start[1]=0.1; goal[0]=goal[1]=0.9;
    setup.setStartAndGoalStates(start,goal); require(static_cast<bool>(setup.solve(1.0)));
    GProp_GProps props; BRepGProp::VolumeProperties(BRepPrimAPI_MakeBox(1,2,3).Shape(),props);
    require(std::abs(props.Mass()-6) < 1e-9);
    qhT context; qhT* qh=&context; qh_zero(qh,stderr);
    coordT points[]={0,0,0, 1,0,0, 0,1,0, 0,0,1}; char flags[]="qhull Qt";
    int code=qh_new_qhull(qh,3,4,points,0,flags,nullptr,stderr); require(code==0);
    qh_freeqhull(qh,!qh_ALL); int current,total; qh_memfreeshort(qh,&current,&total); require(current==0);
}
