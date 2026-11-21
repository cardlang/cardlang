# CMake toolchain file: clang from an llvm-mingw distribution, targeting 64-bit Windows (x86_64-w64-mingw32).
# 64-bit because the harness loads the VM's shared library into the project's 64-bit Python (VM7 §2a).
# LLVM_MINGW_ROOT is the distribution's folder; vm/c/build.py passes it.
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_PROCESSOR x86_64)

if(NOT LLVM_MINGW_ROOT)
    message(FATAL_ERROR "Set LLVM_MINGW_ROOT to the llvm-mingw folder (vm/c/build.py does).")
endif()
set(CMAKE_C_COMPILER "${LLVM_MINGW_ROOT}/bin/x86_64-w64-mingw32-clang.exe")
set(CMAKE_AR "${LLVM_MINGW_ROOT}/bin/llvm-ar.exe")
set(CMAKE_RANLIB "${LLVM_MINGW_ROOT}/bin/llvm-ranlib.exe")
set(CMAKE_RC_COMPILER "${LLVM_MINGW_ROOT}/bin/x86_64-w64-mingw32-windres.exe")
set(CMAKE_TRY_COMPILE_PLATFORM_VARIABLES LLVM_MINGW_ROOT)
