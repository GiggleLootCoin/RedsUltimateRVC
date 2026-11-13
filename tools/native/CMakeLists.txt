cmake_minimum_required(VERSION 3.22.1)
project(red_source_separation LANGUAGES CXX)

add_library(sherpa_onnx_c_api SHARED IMPORTED)
set_target_properties(sherpa_onnx_c_api PROPERTIES
    IMPORTED_LOCATION "${CMAKE_CURRENT_SOURCE_DIR}/../jniLibs/arm64-v8a/libsherpa-onnx-c-api.so")

add_library(red_source_separation SHARED source_separation_jni.cpp)
target_include_directories(red_source_separation PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/include")
target_compile_features(red_source_separation PRIVATE cxx_std_17)
target_compile_options(red_source_separation PRIVATE -O2 -fvisibility=hidden)
target_link_libraries(red_source_separation PRIVATE sherpa_onnx_c_api log)
