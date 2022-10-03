cmake_minimum_required(VERSION 2.8.12)
project(test_package)

list(APPEND CMAKE_PREFIX_PATH ${PROJECT_BINARY_DIR})
list(APPEND CMAKE_MODULE_PATH ${PROJECT_BINARY_DIR})
set(CMAKE_FIND_PACKAGE_PREFER_CONFIG ON)

find_package(caf REQUIRED)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} caf::caf)
set_property(TARGET ${PROJECT_NAME} PROPERTY CXX_STANDARD 11)
