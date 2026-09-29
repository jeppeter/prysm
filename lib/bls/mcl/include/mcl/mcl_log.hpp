#pragma once

#include <stdio.h>
#include <stdlib.h>

#define BN_LOG(...) do{fprintf(stderr,"[%s:%d] ",__FILE__,__LINE__); fprintf(stderr,__VA_ARGS__);fprintf(stderr,"\n");fflush(stderr);} while(0)
