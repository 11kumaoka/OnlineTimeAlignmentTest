cmake_minimum_required(VERSION 3.20)
project(seven_layer_standalone_acts LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(Acts REQUIRED COMPONENTS Core)
find_package(podio REQUIRED)
find_package(EDM4EIC REQUIRED)
find_package(ROOT REQUIRED)

add_executable(seven_layer_acts_fit src/standalone_acts_fit.cpp)

target_link_libraries(seven_layer_acts_fit
  PRIVATE
    Acts::Core
    podio::podioIO
    EDM4EIC::edm4eic
    ROOT::Core
)

target_compile_definitions(seven_layer_acts_fit PRIVATE PODIO_ENABLE_RNTUPLE=1)
