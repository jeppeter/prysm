package main

import (
	_ "fmt"
	"github.com/OffchainLabs/prysm/v7/cmd"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmext/checkenv"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmext/expforkname"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmext/itercfg"
	"github.com/sirupsen/logrus"
	"github.com/urfave/cli/v2"
	"os"
	"strconv"
)

var prysmextCommands []*cli.Command

var appFlags = []cli.Flag{
	cmd.VerbosityFlag,
	cmd.LogfilesFlag,
	cmd.LogappendFlag,
	cmd.LogFormat,
	cmd.ConfigFileFlag,
	// cmd.LoadFlagsFromConfig,
}

var Commands = []*cli.Command{
	{
		Name:   "nlogtst",
		Usage:  "commands for logtst with count",
		Action: logtst_Handler,
	},
}

func main() {
	app := &cli.App{
		Flags:    appFlags,
		Commands: prysmextCommands,
		Before: func(ctx *cli.Context) (err error) {

			err = cmd.LoadLogFlags(ctx, appFlags, true)
			if err != nil {
				return
			}
			return
		},
	}
	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}

func logtst_Handler(ctx *cli.Context) (err error) {
	var cnt int = 10
	var cntstr string
	var i int

	if ctx.Args().Len() > 0 {
		cntstr = ctx.Args().Get(0)
		cnt, err = strconv.Atoi(cntstr)
		if err != nil {
			return
		}
	}

	for i = 0; i < cnt; i += 1 {
		logrus.Errorf("cnt\n%d", i)
		logrus.Debugf("cnt\n%d", i)
		logrus.Infof("cnt\n%d", i)
		logrus.Tracef("cnt\n%d", i)
		logrus.Warnf("cnt\n%d", i)
	}
	err = nil
	return
}

func init() {
	appFlags = cmd.WrapFlags(appFlags)
	prysmextCommands = append(prysmextCommands, checkenv.Commands...)
	prysmextCommands = append(prysmextCommands, expforkname.Commands...)
	prysmextCommands = append(prysmextCommands, Commands...)
	prysmextCommands = append(prysmextCommands, itercfg.Commands...)
}
