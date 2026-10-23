cmake_minimum_required(VERSION 3.22)
project(Scintilla VERSION 5.6.7 LANGUAGES CXX)
find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets)
set(CMAKE_AUTOMOC ON)
add_library(Headers INTERFACE)
add_library(Scintilla::Headers ALIAS Headers)
target_include_directories(Headers INTERFACE $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include> $<INSTALL_INTERFACE:include/scintilla>)
add_library(ScintillaEditBase
    qt/ScintillaEditBase/PlatQt.cpp
    qt/ScintillaEditBase/ScintillaQt.cpp
    qt/ScintillaEditBase/ScintillaEditBase.cpp
    qt/ScintillaEditBase/../../src/XPM.cxx
    qt/ScintillaEditBase/../../src/ViewStyle.cxx
    qt/ScintillaEditBase/../../src/UniqueString.cxx
    qt/ScintillaEditBase/../../src/UniConversion.cxx
    qt/ScintillaEditBase/../../src/UndoHistory.cxx
    qt/ScintillaEditBase/../../src/Style.cxx
    qt/ScintillaEditBase/../../src/Selection.cxx
    qt/ScintillaEditBase/../../src/ScintillaBase.cxx
    qt/ScintillaEditBase/../../src/RunStyles.cxx
    qt/ScintillaEditBase/../../src/RESearch.cxx
    qt/ScintillaEditBase/../../src/PositionCache.cxx
    qt/ScintillaEditBase/../../src/PerLine.cxx
    qt/ScintillaEditBase/../../src/MarginView.cxx
    qt/ScintillaEditBase/../../src/LineMarker.cxx
    qt/ScintillaEditBase/../../src/KeyMap.cxx
    qt/ScintillaEditBase/../../src/Indicator.cxx
    qt/ScintillaEditBase/../../src/Geometry.cxx
    qt/ScintillaEditBase/../../src/EditView.cxx
    qt/ScintillaEditBase/../../src/Editor.cxx
    qt/ScintillaEditBase/../../src/EditModel.cxx
    qt/ScintillaEditBase/../../src/Document.cxx
    qt/ScintillaEditBase/../../src/Decoration.cxx
    qt/ScintillaEditBase/../../src/DBCS.cxx
    qt/ScintillaEditBase/../../src/ContractionState.cxx
    qt/ScintillaEditBase/../../src/CharClassify.cxx
    qt/ScintillaEditBase/../../src/CharacterType.cxx
    qt/ScintillaEditBase/../../src/CharacterCategoryMap.cxx
    qt/ScintillaEditBase/../../src/ChangeHistory.cxx
    qt/ScintillaEditBase/../../src/CellBuffer.cxx
    qt/ScintillaEditBase/../../src/CaseFolder.cxx
    qt/ScintillaEditBase/../../src/CaseConvert.cxx
    qt/ScintillaEditBase/../../src/CallTip.cxx
    qt/ScintillaEditBase/../../src/AutoComplete.cxx
    qt/ScintillaEditBase/ScintillaEditBase.h qt/ScintillaEditBase/ScintillaQt.h)
target_compile_features(ScintillaEditBase PUBLIC cxx_std_17)
target_compile_definitions(ScintillaEditBase PRIVATE SCINTILLA_QT=1 MAKING_LIBRARY=1)
target_link_libraries(ScintillaEditBase PUBLIC Headers Qt6::Core Qt6::Gui Qt6::Widgets)
target_include_directories(ScintillaEditBase PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/src>
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/qt/ScintillaEditBase>
    $<INSTALL_INTERFACE:include/scintilla/internal>)
install(TARGETS Headers ScintillaEditBase EXPORT ScintillaTargets RUNTIME DESTINATION bin LIBRARY DESTINATION lib ARCHIVE DESTINATION lib)
install(DIRECTORY include/ DESTINATION include/scintilla FILES_MATCHING PATTERN "*.h")
install(DIRECTORY src/ DESTINATION include/scintilla/internal FILES_MATCHING PATTERN "*.h")
install(FILES qt/ScintillaEditBase/ScintillaEditBase.h DESTINATION include/scintilla/internal)
include(CMakePackageConfigHelpers)
configure_package_config_file(ScintillaConfig.cmake.in "${CMAKE_CURRENT_BINARY_DIR}/ScintillaConfig.cmake" INSTALL_DESTINATION lib/cmake/Scintilla)
write_basic_package_version_file("${CMAKE_CURRENT_BINARY_DIR}/ScintillaConfigVersion.cmake" VERSION 5.6.7 COMPATIBILITY SameMajorVersion)
install(EXPORT ScintillaTargets NAMESPACE Scintilla:: DESTINATION lib/cmake/Scintilla)
install(FILES "${CMAKE_CURRENT_BINARY_DIR}/ScintillaConfig.cmake" "${CMAKE_CURRENT_BINARY_DIR}/ScintillaConfigVersion.cmake" DESTINATION lib/cmake/Scintilla)
