# The CardLang VM in portable C11 (VM7, plans_and_notes/vm-plans/VM7-c-vm.md).
#
# Built with two compilers, both warning-free (J1): MSVC, and clang from llvm-mingw (cmake/llvm-mingw-x86_64.cmake).
# Use vm/c/build.py, which sets up either toolchain, rather than calling CMake directly.
cmake_minimum_required(VERSION 3.25)
project(cardlang_vm VERSION 1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Warnings are errors on both compilers (VM7 §2, coding rules).
function(cardlang_warnings target)
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4 /WX)
    else()
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic -Werror)
    endif()
endfunction()

# The VM: loader, interpreter and native library. No dynamic allocation, no global state (vm/c/README.md).
add_library(cardlang_vm STATIC src/vm.c src/natives.c src/header_check.c)
target_include_directories(cardlang_vm PUBLIC include)
cardlang_warnings(cardlang_vm)

# The host HAL for tests (VM7 step 2: storage and test hooks; step 3 adds keys and Mbed TLS).
add_library(cardlang_hal_host STATIC hal-host/hal_host.c)
target_include_directories(cardlang_hal_host PUBLIC include hal-host)
cardlang_warnings(cardlang_hal_host)

# The shared library the harness drives through cffi (J3): cvm.dll, or libcvm.so elsewhere.
add_library(cvm SHARED test/cvm.c)
target_link_libraries(cvm PRIVATE cardlang_vm cardlang_hal_host)
set_target_properties(cvm PROPERTIES PREFIX "")
cardlang_warnings(cvm)
