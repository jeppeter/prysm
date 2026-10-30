package randfile

import (
	"fmt"
	"os"
)

type RandFile struct {
	fp     *os.File
	path   string
	bclose bool
}

func (retp *RandFile) Close() {
	if retp.fp != nil && retp.bclose {
		retp.fp.Close()
	}
	retp.fp = nil
	retp.bclose = false
}

func NewRandFp(fp *os.File, note string) (retp *RandFile, err error) {
	retp = &RandFile{}
	retp.fp = fp
	retp.path = note
	retp.bclose = false
	err = nil
	return
}

func NewRandFile(path string) (retp *RandFile, err error) {
	retp = &RandFile{}
	retp.path = path
	retp.bclose = true
	retp.fp, err = os.Open(path)
	if err != nil {
		return
	}
	err = nil
	return
}

func (retp *RandFile) Int63() (retv int64) {
	var cnt int
	var err error
	var inb []byte

	if retp.fp == nil {
		panic(fmt.Sprintf("[%s]alread close ", retp.path))
	}

	inb = make([]byte, 8)
	cnt, err = retp.fp.Read(inb)
	if err != nil {
		panic(fmt.Sprintf("can not read [%s] error %s", retp.path, err.Error()))
	}

	if cnt != 8 {
		panic(fmt.Sprintf("read [%s] %d != 8", retp.path, cnt))
	}
	retv = 0
	for _, v := range inb {
		retv <<= 8
		retv |= int64(v)
	}
	return
}

func (retp *RandFile) Uint64() (retv uint64) {
	var cnt int
	var err error
	var inb []byte
	if retp.fp == nil {
		panic(fmt.Sprintf("[%s]alread close ", retp.path))
	}
	inb = make([]byte, 8)
	cnt, err = retp.fp.Read(inb)
	if err != nil {
		panic(fmt.Sprintf("can not read [%s] error %s", retp.path, err.Error()))
	}

	if cnt != 8 {
		panic(fmt.Sprintf("read [%s] %d != 8", retp.path, cnt))
	}
	retv = 0
	for _, v := range inb {
		retv <<= 8
		retv |= uint64(v)
	}
	return
}

func (retp *RandFile) Seed(_n int64) {
	return
}
