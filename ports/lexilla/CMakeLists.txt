cmake_minimum_required(VERSION 3.22)
project(Lexilla VERSION 5.4.6 LANGUAGES CXX)
find_package(Scintilla CONFIG REQUIRED)
file(GLOB support CONFIGURE_DEPENDS lexlib/*.cxx)
file(GLOB lexers CONFIGURE_DEPENDS lexers/*.cxx)
add_library(Lexilla STATIC src/Lexilla.cxx ${support} ${lexers})
target_compile_features(Lexilla PUBLIC cxx_std_17)
target_compile_definitions(Lexilla PRIVATE SCI_LEXER)
set_target_properties(Lexilla PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_link_libraries(Lexilla PUBLIC Scintilla::Headers)
target_include_directories(Lexilla PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/lexlib>
    $<INSTALL_INTERFACE:include/lexilla>
    $<INSTALL_INTERFACE:include/lexilla/lexlib>)
install(TARGETS Lexilla EXPORT LexillaTargets ARCHIVE DESTINATION lib)
install(DIRECTORY include/ DESTINATION include/lexilla FILES_MATCHING PATTERN "*.h")
install(DIRECTORY lexlib/ DESTINATION include/lexilla/lexlib FILES_MATCHING PATTERN "*.h")
include(CMakePackageConfigHelpers)
configure_package_config_file(LexillaConfig.cmake.in "${CMAKE_CURRENT_BINARY_DIR}/LexillaConfig.cmake" INSTALL_DESTINATION lib/cmake/Lexilla)
write_basic_package_version_file("${CMAKE_CURRENT_BINARY_DIR}/LexillaConfigVersion.cmake" VERSION 5.4.6 COMPATIBILITY SameMajorVersion)
install(EXPORT LexillaTargets NAMESPACE Lexilla:: DESTINATION lib/cmake/Lexilla)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/LexillaConfig.cmake" "${CMAKE_CURRENT_BINARY_DIR}/LexillaConfigVersion.cmake" DESTINATION lib/cmake/Lexilla)
