# The CardLang VM in portable C11 (VM7, plans_and_notes/vm-plans/VM7-c-vm.md).
#
# Built with two compilers, both warning-free (J1): MSVC, and clang from llvm-mingw (cmake/llvm-mingw-x86_64.cmake).
# Use vm/c/build.py, which sets up either toolchain, rather than calling CMake directly.
cmake_minimum_required(VERSION 3.25)
project(cardlang_vm VERSION 1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# Warnings are errors on both compilers (VM7 §2, coding rules).
function(cardlang_warnings target)
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4 /WX)
    else()
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic -Werror)
    endif()
endfunction()

# Step 1: the headers, compiled for the first time (cl_hal.h and cl_hal_test.h, VM2).
add_library(cardlang_vm STATIC src/header_check.c)
target_include_directories(cardlang_vm PUBLIC include)
cardlang_warnings(cardlang_vm)
