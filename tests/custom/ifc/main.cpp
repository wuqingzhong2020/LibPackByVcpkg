extern "C" int ifcopenshell086_check();
extern "C" int ifcopenshell086_check_output();

int main(int argc, char**)
{
    return argc > 1 ? ifcopenshell086_check_output() : ifcopenshell086_check();
}
