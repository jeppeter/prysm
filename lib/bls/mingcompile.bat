
rem set MIN_FLAGS=
set TOPDIR=%~dp0
if Not Exist "%TOPDIR%obj\" (md %TOPDIR%obj)

if  NOT exist "%TOPDIR%lib\" (	md %TOPDIR%lib)

g++.exe -c %TOPDIR%/mcl/src/fp.cpp -o %TOPDIR%/obj/fp.o  -std=c++03 -O3 -DNDEBUG  -DMCL_DONT_USE_OPENSSL -DMCL_SIZEOF_UNIT=8 -DMCL_MAX_BIT_SIZE=384 -DCYBOZU_DONT_USE_EXCEPTION -DCYBOZU_DONT_USE_STRING -I %TOPDIR%/include -I %TOPDIR%/mcl/include -DBLS_ETH=1 
g++.exe -c %TOPDIR%/src/bls_c384_256.cpp -o %TOPDIR%/obj/bls_c384_256.o  -std=c++03 -O3 -DNDEBUG -DMCL_DONT_USE_OPENSSL -DMCL_SIZEOF_UNIT=8 -DMCL_MAX_BIT_SIZE=384 -DCYBOZU_DONT_USE_EXCEPTION -DCYBOZU_DONT_USE_STRING -I %TOPDIR%/include -I %TOPDIR%/mcl/include -DBLS_ETH=1 
g++.exe -c -o %TOPDIR%/obj/bint-asm.o %TOPDIR%/mcl/src/asm/bint-x64-amd64.s
ar.exe r %TOPDIR%/lib/libbls384_256.a %TOPDIR%/obj/fp.o %TOPDIR%/obj/bls_c384_256.o %TOPDIR%/obj/bint-asm.o

