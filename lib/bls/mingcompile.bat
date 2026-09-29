
rem set MIN_FLAGS=
g++.exe -c ./mcl/src/fp.cpp -o ./obj/fp.o  -std=c++03 -O3 -DNDEBUG -fPIC -DMCL_DONT_USE_OPENSSL -DMCL_SIZEOF_UNIT=8 -DMCL_MAX_BIT_SIZE=384 -DCYBOZU_DONT_USE_EXCEPTION -DCYBOZU_DONT_USE_STRING -I ./include -I ./mcl/include -DBLS_ETH=1 
g++.exe -c ./src/bls_c384_256.cpp -o ./obj/bls_c384_256.o  -std=c++03 -O3 -DNDEBUG -fPIC -DMCL_DONT_USE_OPENSSL -DMCL_SIZEOF_UNIT=8 -DMCL_MAX_BIT_SIZE=384 -DCYBOZU_DONT_USE_EXCEPTION -DCYBOZU_DONT_USE_STRING -I ./include -I ./mcl/include -DBLS_ETH=1 
g++.exe -c -o ./obj/bint-asm.o ./mcl/src/asm/bint-x64-amd64.s
ar.exe r ./lib/libbls384_256.a ./obj/fp.o ./obj/bls_c384_256.o ./obj/bint-asm.o