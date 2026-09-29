#include <iostream>
#define MCLBN_FP_UNIT_SIZE 6
#define MCLBN_FR_UNIT_SIZE 4

#include <bls/bls.h>

int main(int argc,char* argv[]) 
{
	int ret = blsInit(5,MCLBN_COMPILED_TIME_VAR);
	fprintf(stdout,"ret %d\n",ret);
	return 0;
}