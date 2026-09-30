#pragma once

#include <stdio.h>
#include <stdlib.h>
#if 0
#define BN_LOG(...) do{fprintf(stderr,"[%s:%d] ",__FILE__,__LINE__); fprintf(stderr,__VA_ARGS__);fprintf(stderr,"\n");fflush(stderr);} while(0)
#define BN_BUFFER_LOG(ptr,size,...)                                                               \
do{                                                                                               \
	unsigned char* _ptr = (unsigned char*)(ptr);                                                  \
	int _size = (int) (size);                                                                     \
	int _i;                                                                                       \
	int _lasti=0;                                                                                 \
	fprintf(stderr,"[%s:%d] ", __FILE__,__LINE__);                                                \
	fprintf(stderr,__VA_ARGS__);                                                                  \
	for(_i=0;_i < _size;_i++) {                                                                   \
		if ((_i % 16) == 0) {                                                                     \
			if (_i > 0) {                                                                         \
				fprintf(stderr,"    ");                                                           \
				while(_lasti < _i) {                                                              \
					if (_ptr[_lasti] >= ' ' && _ptr[_lasti] <= '~') {                             \
						fprintf(stderr,"%c", _ptr[_lasti]);                                       \
					} else {                                                                      \
						fprintf(stderr,".");                                                      \
					}                                                                             \
					_lasti ++;                                                                    \
				}                                                                                 \
			}                                                                                     \
			fprintf(stderr,"\n");                                                                 \
			fprintf(stderr,"0x%08x:",_i);                                                         \
		}                                                                                         \
		fprintf(stderr," 0x%02x",_ptr[_i]);                                                       \
	}                                                                                             \
	if (_lasti != _i) {                                                                           \
		while((_i % 16) != 0) {                                                                   \
			fprintf(stderr,"     ");                                                              \
			_i ++;                                                                                \
		}                                                                                         \
		fprintf(stderr,"    ");                                                                   \
		while(_lasti < _size) {                                                                   \
			if (_ptr[_lasti] >= ' ' && _ptr[_lasti] <= '~') {                                     \
				fprintf(stderr,"%c", _ptr[_lasti]);                                               \
			} else {                                                                              \
				fprintf(stderr,".");                                                              \
			}                                                                                     \
			_lasti++;                                                                             \
		}                                                                                         \
	}                                                                                             \
	fprintf(stderr,"\n");	                                                                      \
}while(0)

#else
#define BN_LOG(...) do{} while(0)
#define BN_BUFFER_LOG(ptr,size,...)     do{}while(0)

#endif