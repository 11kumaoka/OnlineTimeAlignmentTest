cmake_minimum_required(VERSION 3.20)
project(local_eicrecon LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

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
set(MILLEPEDE_PREFIX "${CMAKE_CURRENT_SOURCE_DIR}/../millepede/install/millepede-ii" CACHE PATH "Path to local millepede-ii installation")

if(ENABLE_MILLEPEDE)
  list(APPEND CMAKE_PREFIX_PATH "${MILLEPEDE_PREFIX}")
  find_package(Mille CONFIG REQUIRED)
endif()

add_library(BeamTestReco SHARED
  plugins/BeamTestReco.cc
  algorithms/digi/SiliconTrackerDigi.cc
  algorithms/tracking/TrackerHitReconstruction.cc
  algorithms/tracking/BeamTestACTSFitter.cc
  processors/BeamTestEventProcessor.cc
  processors/BeamTestMilleProcessor.cc
  ../millepede/src/BeamTestMilleWriter.cc
)

# Local copied headers first, then installed EICrecon framework headers.
target_include_directories(BeamTestReco
  PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/../millepede/src
    /opt/local/include/EICrecon
)

target_link_libraries(BeamTestReco
  PRIVATE
    JANA::jana2_shared_lib
    fmt::fmt
    spdlog::spdlog
    DD4hep::DDCore
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
