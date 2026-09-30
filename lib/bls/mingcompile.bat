
rem set MIN_FLAGS=
set TOPDIR=%~dp0
set COMPILE_CONFIG=-std=c++03 -O3 -DNDEBUG  -DMCL_DONT_USE_OPENSSL -DMCL_SIZEOF_UNIT=8 -DMCL_MAX_BIT_SIZE=384 -DCYBOZU_DONT_USE_EXCEPTION -DCYBOZU_DONT_USE_STRING -I %TOPDIR%/include -I %TOPDIR%/mcl/include -DBLS_ETH=1  -DWINDOWS_DEFINE -DMCL_BINT_ASM=0
if Not Exist "%TOPDIR%win\obj\" (md %TOPDIR%win\obj)

if  NOT exist "%TOPDIR%win\lib\" (	md %TOPDIR%win\lib)

g++.exe -c %TOPDIR%/mcl/src/fp.cpp -o %TOPDIR%win/obj/fp.o  %COMPILE_CONFIG%
g++.exe -c %TOPDIR%/src/bls_c384_256.cpp -o %TOPDIR%win/obj/bls_c384_256.o  %COMPILE_CONFIG%
g++.exe -c -o %TOPDIR%win/obj/bint-asm.o %TOPDIR%/mcl/src/asm/bint-x64-amd64.s
ar.exe r %TOPDIR%win/lib/libbls384_256.a %TOPDIR%win/obj/fp.o %TOPDIR%win/obj/bls_c384_256.o %TOPDIR%win/obj/bint-asm.o

