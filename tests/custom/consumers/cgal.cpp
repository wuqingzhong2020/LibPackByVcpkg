#include <CGAL/Simple_cartesian.h>
#include <CGAL/squared_distance_3.h>
#include <CGAL/Polygon_2.h>
#include <gmp.h>
#include <mpfr.h>
#include <stdexcept>
int main() {
    using K=CGAL::Simple_cartesian<double>;
    if(CGAL::squared_distance(K::Point_3(0,0,0),K::Point_3(1,2,2))!=9) return 1;
    CGAL::Polygon_2<K> polygon; polygon.push_back({0,0}); polygon.push_back({2,0}); polygon.push_back({0,2});
    if(polygon.area()!=2) return 2;
    mpz_t z; mpz_init_set_ui(z,7); mpz_mul(z,z,z); bool ok=mpz_cmp_ui(z,49)==0; mpz_clear(z);
    mpfr_t number; mpfr_init2(number,128); mpfr_set_ui(number,49,MPFR_RNDN); mpfr_sqrt(number,number,MPFR_RNDN);
    ok=ok && mpfr_cmp_ui(number,7)==0; mpfr_clear(number);
    if(!ok) throw std::runtime_error("GMP/MPFR exact arithmetic");
}
