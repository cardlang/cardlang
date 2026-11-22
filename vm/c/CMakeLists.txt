# The CardLang VM in portable C11.
#
# Built with two compilers, both warning-free: MSVC, and a MinGW-w64 clang such as llvm-mingw's.
# Use vm/c/build.py, which sets up either toolchain, rather than calling CMake directly.
cmake_minimum_required(VERSION 3.25)
project(cardlang_vm VERSION 1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Warnings are errors on both compilers (coding rules).
function(cardlang_warnings target)
    if(MSVC)
        target_compile_options(${target} PRIVATE /W4 /WX)
    else()
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic -Werror)
    endif()
endfunction()

# Mbed TLS, the host HAL's crypto backend: the 3.6 LTS release archive, downloaded once into build/downloads
# (shared by both toolchains' build trees, git-ignored) and checked against the SHA-256 the release publishes.
include(FetchContent)
set(MBEDTLS_VERSION 3.6.8)
set(MBEDTLS_SHA256 bc54b818e87f49c0b3281dd85d24adaede0e63b4e822e3fbd49c005a38b9595b)
set(MBEDTLS_ARCHIVE ${CMAKE_CURRENT_SOURCE_DIR}/build/downloads/mbedtls-${MBEDTLS_VERSION}.tar.bz2)
file(DOWNLOAD
    https://github.com/Mbed-TLS/mbedtls/releases/download/mbedtls-${MBEDTLS_VERSION}/mbedtls-${MBEDTLS_VERSION}.tar.bz2
    ${MBEDTLS_ARCHIVE} EXPECTED_HASH SHA256=${MBEDTLS_SHA256} TLS_VERIFY ON)
set(ENABLE_TESTING OFF CACHE BOOL "" FORCE)
set(ENABLE_PROGRAMS OFF CACHE BOOL "" FORCE)
set(MBEDTLS_FATAL_WARNINGS OFF CACHE BOOL "" FORCE)
set(GEN_FILES OFF CACHE BOOL "" FORCE)
set(USE_SHARED_MBEDTLS_LIBRARY OFF CACHE BOOL "" FORCE)
set(USE_STATIC_MBEDTLS_LIBRARY ON CACHE BOOL "" FORCE)
set(DISABLE_PACKAGE_CONFIG_AND_INSTALL ON CACHE BOOL "" FORCE)
FetchContent_Declare(mbedtls URL ${MBEDTLS_ARCHIVE} URL_HASH SHA256=${MBEDTLS_SHA256} EXCLUDE_FROM_ALL)
FetchContent_MakeAvailable(mbedtls)

# The host's operation context (HAL-27): a PSA hash or MAC operation with Mbed TLS's default configuration, 416
# bytes on 64-bit hosts. hal_host.c checks that it fits.
set(CARDLANG_HOST_OP_CTX_SIZE 416)

# The VM: loader, interpreter and native library. No dynamic allocation, no global state (vm/c/README.md).
# This build includes the test-only catalog (V-33).
add_library(cardlang_vm STATIC src/vm.c src/natives.c src/header_check.c)
target_include_directories(cardlang_vm PUBLIC include)
target_compile_definitions(cardlang_vm PUBLIC CL_HAL_OP_CTX_SIZE=${CARDLANG_HOST_OP_CTX_SIZE}u PRIVATE CL_TEST_CATALOG=1)
cardlang_warnings(cardlang_vm)

# The host HAL for tests: storage, keys, crypto through Mbed TLS, and the test hooks.
add_library(cardlang_hal_host STATIC hal-host/hal_host.c)
target_include_directories(cardlang_hal_host PUBLIC include hal-host)
target_compile_definitions(cardlang_hal_host PUBLIC CL_HAL_OP_CTX_SIZE=${CARDLANG_HOST_OP_CTX_SIZE}u)
target_link_libraries(cardlang_hal_host PUBLIC mbedcrypto)
cardlang_warnings(cardlang_hal_host)

# The shared library the harness drives through cffi: cvm.dll, or libcvm.so elsewhere.
add_library(cvm SHARED test/cvm.c)
target_link_libraries(cvm PRIVATE cardlang_vm cardlang_hal_host)
set_target_properties(cvm PROPERTIES PREFIX "")
cardlang_warnings(cvm)
