cmake_minimum_required(VERSION 3.20)
project(local_eicrecon LANGUAGES CXX)
get_filename_component(TESTBENCH_CMAKE_FILE "${CMAKE_CURRENT_LIST_FILE}" REALPATH)
get_filename_component(TESTBENCH_SOURCE_DIR "${TESTBENCH_CMAKE_FILE}" DIRECTORY)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_path(EICRECON_INCLUDE_DIR extensions/jana/JOmniFactory.h
  HINTS "$ENV{EICrecon_ROOT}/include/EICrecon" /opt/local/include/EICrecon REQUIRED)
find_package(JANA REQUIRED)
find_package(algorithms REQUIRED COMPONENTS Core)
find_package(Microsoft.GSL REQUIRED)
find_package(fmt REQUIRED)
find_package(spdlog REQUIRED)
find_package(DD4hep REQUIRED)
find_package(Acts REQUIRED COMPONENTS Core)
find_package(podio REQUIRED)
find_package(EDM4HEP REQUIRED)
find_package(EDM4EIC REQUIRED)

option(ENABLE_MILLEPEDE "Enable Millepede/Mille integration in local plugin" ON)
if(NOT ENABLE_MILLEPEDE)
  message(FATAL_ERROR "This plugin requires Mille; build the documented dependencies first")
endif()
set(MILLEPEDE_PREFIX "${TESTBENCH_SOURCE_DIR}/../external/install" CACHE PATH "Path to local millepede-ii installation")

if(ENABLE_MILLEPEDE)
  list(APPEND CMAKE_PREFIX_PATH "${MILLEPEDE_PREFIX}")
  # Pin package discovery as well as the prefix: an old Mille_DIR cache otherwise wins.
  set(Mille_DIR "${MILLEPEDE_PREFIX}/cmake" CACHE PATH "Mille config in the selected installation" FORCE)
  find_package(Mille CONFIG REQUIRED PATHS "${MILLEPEDE_PREFIX}/cmake" NO_DEFAULT_PATH)
endif()

add_library(BeamTestReco SHARED
  plugins/BeamTestReco.cc
  algorithms/digi/SiliconTrackerDigi.cc
  algorithms/tracking/TrackerHitReconstruction.cc
  algorithms/tracking/BeamTestACTSFitter.cc
  processors/BeamTestEventProcessor.cc
  processors/BeamTestMilleProcessor.cc
  ${TESTBENCH_SOURCE_DIR}/alignment/src/BeamTestMilleWriter.cc
)

# Local copied headers first, then installed EICrecon framework headers.
target_include_directories(BeamTestReco
  PRIVATE
    ${TESTBENCH_SOURCE_DIR}
    ${TESTBENCH_SOURCE_DIR}/alignment/src
    ${EICRECON_INCLUDE_DIR}
)

target_link_libraries(BeamTestReco
  PRIVATE
    JANA::jana2_shared_lib
    fmt::fmt
    spdlog::spdlog
    DD4hep::DDCore
    DD4hep::DDRec
    Acts::Core
    podio::podioIO
    EDM4HEP::edm4hep
    EDM4EIC::edm4eic
    algorithms::core
)

if(ENABLE_MILLEPEDE)
  target_link_libraries(BeamTestReco PRIVATE Mille2)
  target_compile_definitions(BeamTestReco PRIVATE LOCAL_EICRECON_WITH_MILLEPEDE=1)
endif()

target_compile_definitions(BeamTestReco PRIVATE USE_MODERN_PODIO_GLUE=1)

set_target_properties(BeamTestReco PROPERTIES
  PREFIX ""
  OUTPUT_NAME "BeamTestReco"
)

# Focused extension of the upstream builder: independent Global Y translation.
add_library(LocalTelescopeGeometry SHARED geometry/SiTrackerEndcap2XY_geo.cpp)
target_link_libraries(LocalTelescopeGeometry PRIVATE DD4hep::DDCore)
dd4hep_generate_rootmap(LocalTelescopeGeometry)

# Isolated compatibility probe: never changes BeamTestReco or its default geometry.
option(TESTBENCH_BUILD_OFFICIAL_GEOMETRY_PROBE "Build the installed EICrecon Geometry compatibility probe" OFF)
if(TESTBENCH_BUILD_OFFICIAL_GEOMETRY_PROBE)
  find_package(Acts REQUIRED COMPONENTS PluginDD4hep)
  find_package(nlohmann_json CONFIG REQUIRED)
  find_package(EICrecon CONFIG REQUIRED)
  add_executable(TelescopeGeometryProbe geometry/OfficialGeometryProbe.cc)
  target_include_directories(TelescopeGeometryProbe PRIVATE
    ${TESTBENCH_SOURCE_DIR} ${EICRECON_INCLUDE_DIR})
  target_compile_definitions(TelescopeGeometryProbe PRIVATE Acts_VERSION_MAJOR=${Acts_VERSION_MAJOR})
  target_link_libraries(TelescopeGeometryProbe PRIVATE
    EICrecon::algorithms_tracking_library Acts::Core Acts::PluginDD4hep nlohmann_json::nlohmann_json
    DD4hep::DDCore DD4hep::DDRec fmt::fmt spdlog::spdlog)
endif()

# Explicit experimental provider; default reconstruction remains local.
option(TESTBENCH_ENABLE_BLUEPRINT_PROVIDER "Enable converted Gen3 telescope surfaces in BeamTestReco" OFF)
if(TESTBENCH_ENABLE_BLUEPRINT_PROVIDER)
  find_package(Acts REQUIRED COMPONENTS PluginDD4hep)
  target_link_libraries(BeamTestReco PRIVATE Acts::PluginDD4hep)
  target_compile_definitions(BeamTestReco PRIVATE TESTBENCH_BLUEPRINT_PROVIDER=1)
endif()
