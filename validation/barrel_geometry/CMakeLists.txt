cmake_minimum_required(VERSION 3.16)
project(BarrelGeometryDiagnostic LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
find_package(Acts REQUIRED COMPONENTS PluginDD4hep)
find_package(DD4hep REQUIRED COMPONENTS DDCore DDRec)
find_package(EICrecon CONFIG REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(fmt REQUIRED)
find_package(spdlog REQUIRED)
add_executable(BarrelGeometryProbe BarrelGeometryProbe.cc)
target_compile_definitions(BarrelGeometryProbe PRIVATE Acts_VERSION_MAJOR=${Acts_VERSION_MAJOR})
target_link_libraries(BarrelGeometryProbe PRIVATE
  EICrecon::algorithms_tracking_library Acts::Core Acts::PluginDD4hep
  nlohmann_json::nlohmann_json DD4hep::DDCore DD4hep::DDRec fmt::fmt spdlog::spdlog)
