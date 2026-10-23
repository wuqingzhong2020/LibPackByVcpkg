#include <pinocchio/parsers/urdf.hpp>
#include <pinocchio/algorithm/kinematics.hpp>
#include <pinocchio/algorithm/rnea.hpp>
#include <coal/collision.h>
#include <coal/shape/geometric_shapes.h>
#include <cmath>
#include <stdexcept>
#include <iostream>
#ifndef PINOCCHIO_WITH_URDFDOM
#error Pinocchio target must export URDFDOM support
#endif
void require(bool ok,const char* message) { if(!ok) throw std::runtime_error(message); }
int main() {
    pinocchio::Model model; pinocchio::urdf::buildModel(SDK_URDF,model);
    require(model.nq==1 && model.nv==1 && model.njoints==2,"URDF model dimensions");
    require(model.names[1]=="hinge" && std::abs(model.inertias[1].mass()-1)<1e-12,"URDF inertia/joint");
    pinocchio::Data data(model); Eigen::VectorXd q(1); q[0]=std::acos(-1.0)/2;
    pinocchio::forwardKinematics(model,data,q);
    require((data.oMi[1].translation()-Eigen::Vector3d(1,0,0)).norm()<1e-10,"URDF origin/FK");
    require((data.oMi[1].rotation()*Eigen::Vector3d::UnitX()-Eigen::Vector3d::UnitY()).norm()<1e-10,"URDF axis/FK");
    Eigen::VectorXd zero=Eigen::VectorXd::Zero(1);
    require(pinocchio::rnea(model,data,q,zero,zero).allFinite(),"RNEA");
    bool rejected=false;
    try { pinocchio::Model invalid; pinocchio::urdf::buildModelFromXML("<robot/>",invalid); }
    catch(const std::exception&) { rejected=true; }
    require(rejected,"Invalid URDF must be rejected");
    coal::Sphere sphere(1); coal::Transform3s first=coal::Transform3s::Identity(),second=first;
    second.setTranslation(coal::Vec3s(1,0,0)); coal::CollisionRequest request; coal::CollisionResult result;
    coal::collide(&sphere,first,&sphere,second,request,result); require(result.isCollision(),"Coal collision");
    std::cout<<"URDFDOM model, FK, dynamics and Coal passed\n";
}
