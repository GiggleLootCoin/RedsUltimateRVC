cmake_minimum_required(VERSION 3.22)
project(RedRvcGgmlAndroid LANGUAGES C CXX)

if(NOT DEFINED RVC_GGML_SOURCE_DIR)
    message(FATAL_ERROR "RVC_GGML_SOURCE_DIR must point to the pinned rvc-ggml/rvc-ggml source directory")
endif()

set(RVC_VULKAN OFF CACHE BOOL "" FORCE)
set(RVC_CUDA OFF CACHE BOOL "" FORCE)
set(GGML_VULKAN OFF CACHE BOOL "" FORCE)
set(GGML_CUDA OFF CACHE BOOL "" FORCE)
set(GGML_OPENMP OFF CACHE BOOL "" FORCE)
set(GGML_NATIVE OFF CACHE BOOL "" FORCE)
set(GGML_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(GGML_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(GGML_BUILD_SERVER OFF CACHE BOOL "" FORCE)

add_subdirectory("${RVC_GGML_SOURCE_DIR}" "${CMAKE_BINARY_DIR}/rvc-ggml")

add_library(red_rvc_ggml SHARED ../rvc_ggml_jni.cpp)
target_include_directories(red_rvc_ggml PRIVATE
    "${RVC_GGML_SOURCE_DIR}/include"
    "${RVC_GGML_SOURCE_DIR}/src"
)
target_compile_features(red_rvc_ggml PRIVATE cxx_std_20)
target_link_libraries(red_rvc_ggml PRIVATE rvc_core log android)
