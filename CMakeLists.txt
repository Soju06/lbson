cmake_minimum_required(VERSION 3.15...3.27)

project(${SKBUILD_PROJECT_NAME} VERSION ${SKBUILD_PROJECT_VERSION} LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_INTERPROCEDURAL_OPTIMIZATION ON)

if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" OR CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    set(OPTIMIZATION_FLAGS
        -O3
        -DNDEBUG
        -march=native
        -mtune=native
        -flto
        -funroll-loops
        -finline-functions
        -fomit-frame-pointer
    )

    if(CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
        list(APPEND OPTIMIZATION_FLAGS -fvectorize -fslp-vectorize)
    endif()

    if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
        list(APPEND OPTIMIZATION_FLAGS -fgraphite-identity -floop-nest-optimize)
    endif()

elseif(CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
    set(OPTIMIZATION_FLAGS
        /O2
        /Ob2
        /DNDEBUG
        /GL
    )
endif()

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

execute_process(
    COMMAND ${Python_EXECUTABLE} -m setuptools_scm --force-write-version-files
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    RESULT_VARIABLE SETUPTOOLS_SCM_RESULT
    OUTPUT_QUIET
    ERROR_QUIET
)

file(GLOB CORE_SOURCES "src/core/*.cpp" "src/core/*.c")
python_add_library(_core MODULE ${CORE_SOURCES} WITH_SOABI)
target_link_libraries(_core PRIVATE pybind11::headers)

target_compile_definitions(_core PRIVATE VERSION_INFO=${PROJECT_VERSION})
target_include_directories(_core PRIVATE src/core)

target_compile_options(_core PRIVATE ${OPTIMIZATION_FLAGS})

set_property(TARGET _core PROPERTY INTERPROCEDURAL_OPTIMIZATION TRUE)

if(CMAKE_BUILD_TYPE STREQUAL "Release")
    if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" OR CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
        target_link_options(_core PRIVATE -s)
    endif()
endif()

install(TARGETS _core DESTINATION lbson)

if(EXISTS ${CMAKE_SOURCE_DIR}/src/lbson/_version.py)
    install(FILES src/lbson/_version.py DESTINATION lbson)
endif()
