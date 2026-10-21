cmake_minimum_required(VERSION 3.20)
project(beamtest_millepede_tools LANGUAGES CXX)
get_filename_component(ALIGNMENT_CMAKE_FILE "${CMAKE_CURRENT_LIST_FILE}" REALPATH)
get_filename_component(ALIGNMENT_SOURCE_DIR "${ALIGNMENT_CMAKE_FILE}" DIRECTORY)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

set(MILLEPEDE_PREFIX "${ALIGNMENT_SOURCE_DIR}/../../external/install" CACHE PATH "Path to local millepede-ii installation")
list(APPEND CMAKE_PREFIX_PATH "${MILLEPEDE_PREFIX}")
# Pin package discovery as well as the prefix: an old Mille_DIR cache otherwise wins.
set(Mille_DIR "${MILLEPEDE_PREFIX}/cmake" CACHE PATH "Mille config in the selected installation" FORCE)
find_package(Mille CONFIG REQUIRED PATHS "${MILLEPEDE_PREFIX}/cmake" NO_DEFAULT_PATH)

add_library(BeamTestMilleWriter STATIC
  ${ALIGNMENT_SOURCE_DIR}/src/BeamTestMilleWriter.cc
)

target_include_directories(BeamTestMilleWriter
  PUBLIC
    ${ALIGNMENT_SOURCE_DIR}/src
)

target_link_libraries(BeamTestMilleWriter
  PUBLIC
    Mille2
)
