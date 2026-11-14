cmake_minimum_required(VERSION 3.22.1)
project(red_rvc_pth_core C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

if(NOT DEFINED SPARTACVC_SOURCE_DIR)
  message(FATAL_ERROR "SPARTACVC_SOURCE_DIR is required")
endif()

set(SPARTACVC_SRC "${SPARTACVC_SOURCE_DIR}/src")
set(PTH_CORE_SOURCES
  "${SPARTACVC_SRC}/debug.c"
  "${SPARTACVC_SRC}/pickle.c"
  "${SPARTACVC_SRC}/zip_reader.c"
  "${SPARTACVC_SRC}/pth_loader.c"
  "${SPARTACVC_SRC}/rvc.c"
  "${SPARTACVC_SRC}/rvc_infer.c"
  "${SPARTACVC_SRC}/tensor.c"
  "${CMAKE_CURRENT_LIST_DIR}/threads_android.c"
)

add_library(red_rvc_pth_core STATIC ${PTH_CORE_SOURCES})
target_include_directories(red_rvc_pth_core PUBLIC "${SPARTACVC_SRC}")
target_compile_definitions(red_rvc_pth_core PRIVATE _FILE_OFFSET_BITS=64)
target_compile_options(red_rvc_pth_core PRIVATE -include unistd.h)
find_package(Threads REQUIRED)
target_link_libraries(red_rvc_pth_core PUBLIC m Threads::Threads)
