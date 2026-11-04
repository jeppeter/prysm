package checkenv

import (
	"fmt"
	"github.com/OffchainLabs/prysm/v7/crypto/bls/blst"
	"github.com/herumi/bls-eth-go-binary/bls"
	"github.com/urfave/cli/v2"
	"os"
	"path"
	"path/filepath"
	"runtime"
	"strings"
)

var Commands = []*cli.Command{
	{
		Name:    "checkenv",
		Aliases: []string{"chkenv"},
		Usage:   "commands for check environment for compile",
		Action:  checkenv_Handler,
	},
}

func GetExeFile() (exename string, err error) {
	var paths []string
	var envpath string
	var curpath string
	var wholepath string
	var finfo os.FileInfo
	err = nil
	exename = ""
	exename, err = filepath.Abs(os.Args[0])
	if err == nil {
		finfo, err = os.Stat(exename)
		if err == nil && !finfo.IsDir() && finfo.Size() > 0 {
			return
		}
	}

	/*it may be called by the path*/
	envpath = os.Getenv("PATH")
	if len(envpath) == 0 {
		err = fmt.Errorf("can not get PATH")
		return
	}

	if runtime.GOOS == "windows" {
		paths = strings.Split(envpath, ";")
	} else {
		paths = strings.Split(envpath, ":")
	}
	for _, curpath = range paths {
		wholepath = path.Join(curpath, os.Args[0])
		finfo, err = os.Stat(wholepath)
		if err != nil {
			continue
		}
		if !finfo.IsDir() && finfo.Size() > 0 {
			exename = wholepath
			err = nil
			return
		}
	}
	exename = ""
	err = fmt.Errorf("can not get exe from path")
	return
}

func check_blst_verify() (err error) {
	err = nil
	defer func() {
		if err2 := recover(); err2 != nil {
			log.Errorf("recover error %v", err2)
			err = fmt.Errorf("%v", err2)
		}
	}()
	priv, err := blst.RandKey()
	if err != nil {
		return
	}
	pub := priv.PublicKey()
	msg := []byte("hello")
	sig := priv.Sign(msg)
	ok := sig.Verify(pub, msg)
	if !ok {
		err = fmt.Errorf("can not verify blst")
		return
	}
	return

}

func GetExeDir() (dirname string, err error) {
	var exename string
	exename, err = GetExeFile()
	if err != nil {
		return
	}
	dirname = filepath.Dir(exename)
	return
}

func checkenv_Handler(ctx *cli.Context) (err error) {
	if err = bls.Init(bls.BLS12_381); err != nil {
		var curdir string
		curdir, err = GetExeDir()
		if err != nil {
			return
		}
		compilepath := filepath.Join(curdir, "..", "..", "lib", "bls", "mingcompile.bat")
		binpath := filepath.Join(curdir, "..", "..", "lib", "bls", "win", "obj", "libbls384_256.a")
		err = fmt.Errorf("to run %s and copy the %s to the github.com/herumi/bls-eth-go-binary@xx.xx.xx/bls/lib/windows/amd64 xx.xx.xx is the version number", compilepath, binpath)
		return
	}
	if err = bls.SetETHmode(bls.EthModeDraft07); err != nil {
		return
	}
	// Check subgroup order for pubkeys and signatures.
	bls.VerifyPublicKeyOrder(true)
	bls.VerifySignatureOrder(true)

	err = check_blst_verify()
	if err != nil {
		err = fmt.Errorf("please set CGO_CFLAGS=-D__BLST_PORTABLE__")
		return
	}
	err = nil
	return
}
