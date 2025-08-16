cmake_minimum_required(VERSION 3.16)
project(CClean)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(MSVC)
    add_compile_options(/W4)
    add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
else()
    add_compile_options(-Wall -Wextra -pedantic)
endif()

set(SOURCES
    src/main.cpp
    src/cleaner.cpp
    src/utils.cpp
    src/logger.cpp
)

set(HEADERS
    include/config.h
    include/cleaner.h
    include/utils.h
    include/logger.h
)

include_directories(include)

add_executable(cclean ${SOURCES} ${HEADERS})

if(WIN32)
    target_link_libraries(cclean shell32 ole32 shlwapi)
endif()