cmake_minimum_required(VERSION 3.20)
project(beamtest_millepede_tools LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(MILLEPEDE_PREFIX "${CMAKE_CURRENT_SOURCE_DIR}/install/millepede-ii" CACHE PATH "Path to local millepede-ii installation")
list(APPEND CMAKE_PREFIX_PATH "${MILLEPEDE_PREFIX}")
find_package(Mille CONFIG REQUIRED)

add_library(BeamTestMilleWriter STATIC
  src/BeamTestMilleWriter.cc
)

target_include_directories(BeamTestMilleWriter
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries(BeamTestMilleWriter
  PUBLIC
    Mille2
)

add_executable(beamtest_mille_toy
  src/beamtest_mille_toy.cc
)

target_link_libraries(beamtest_mille_toy
  PRIVATE
    BeamTestMilleWriter
)
