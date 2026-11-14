cmake_minimum_required(VERSION 3.22.1)
project(red_rvc_pth_android C CXX)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT DEFINED SPARTACVC_SOURCE_DIR)
  message(FATAL_ERROR "SPARTACVC_SOURCE_DIR is required")
endif()
if(NOT DEFINED ONNXRUNTIME_INCLUDE_DIR OR NOT DEFINED ONNXRUNTIME_LIBRARY)
  message(FATAL_ERROR "ONNXRUNTIME_INCLUDE_DIR and ONNXRUNTIME_LIBRARY are required")
endif()

set(SPARTACVC_SRC "${SPARTACVC_SOURCE_DIR}/src")
set(PTH_NATIVE_SOURCES
  "${SPARTACVC_SRC}/debug.c"
  "${SPARTACVC_SRC}/pickle.c"
  "${SPARTACVC_SRC}/zip_reader.c"
  "${SPARTACVC_SRC}/pth_loader.c"
  "${SPARTACVC_SRC}/rvc.c"
  "${SPARTACVC_SRC}/rvc_infer.c"
  "${SPARTACVC_SRC}/tensor.c"
  "${SPARTACVC_SRC}/mel.c"
  "${SPARTACVC_SRC}/f0.c"
  "${SPARTACVC_SRC}/onnx.c"
  "${CMAKE_CURRENT_LIST_DIR}/threads_android.c"
  "${CMAKE_CURRENT_LIST_DIR}/pth_pipeline.c"
  "${CMAKE_CURRENT_LIST_DIR}/pth_jni.cpp"
)

add_library(red_rvc_pth SHARED ${PTH_NATIVE_SOURCES})
target_include_directories(red_rvc_pth PRIVATE
  "${SPARTACVC_SRC}"
  "${CMAKE_CURRENT_LIST_DIR}"
  "${ONNXRUNTIME_INCLUDE_DIR}"
)
target_compile_definitions(red_rvc_pth PRIVATE _FILE_OFFSET_BITS=64)
target_compile_options(red_rvc_pth PRIVATE -include unistd.h)
find_package(Threads REQUIRED)
add_library(onnxruntime SHARED IMPORTED)
set_target_properties(onnxruntime PROPERTIES IMPORTED_LOCATION "${ONNXRUNTIME_LIBRARY}")
find_library(ANDROID_LOG_LIB log)
target_link_libraries(red_rvc_pth PRIVATE onnxruntime m Threads::Threads ${ANDROID_LOG_LIB})
