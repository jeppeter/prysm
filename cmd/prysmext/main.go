package main

import (
	"github.com/OffchainLabs/prysm/v7/cmd"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmext/checkenv"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmext/expforkname"
	"github.com/sirupsen/logrus"
	"github.com/urfave/cli/v2"
	"io"
	"os"
	"strconv"
)

var prysmextCommands []*cli.Command

var logfilesFlag = &cli.StringSliceFlag{
	Name:  "log.files",
	Usage: "for log files by comma seperate",
}

var appFlags = []cli.Flag{
	cmd.VerbosityFlag,
	logfilesFlag,
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
			verbose := ctx.String(cmd.VerbosityFlag.Name)
			if verbose == "trace" || verbose == "info" || verbose == "warn" {
				logrus.SetReportCaller(true)
			}
			verboselevel, err := logrus.ParseLevel(verbose)
			if err != nil {
				return
			}
			logrus.SetLevel(verboselevel)
			logfs := ctx.StringSlice(logfilesFlag.Name)
			if len(logfs) > 0 {
				var outf []io.Writer = []io.Writer{}

				for _, n := range logfs {
					var curf *os.File
					curf, err = os.OpenFile(n, os.O_CREATE|os.O_WRONLY, 0644)
					if err != nil {
						return
					}
					outf = append(outf, curf)
				}
				outf = append(outf, os.Stderr)
				logrus.SetOutput(io.MultiWriter(outf...))
			} else {
				logrus.SetOutput(os.Stderr)
			}

			err = nil
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
		logrus.Errorf("cnt %d", i)
		logrus.Debugf("cnt %d", i)
		logrus.Infof("cnt %d", i)
		logrus.Tracef("cnt %d", i)
		logrus.Warnf("cnt %d", i)
	}
	err = nil
	return
}

func init() {
	prysmextCommands = append(prysmextCommands, checkenv.Commands...)
	prysmextCommands = append(prysmextCommands, expforkname.Commands...)
	prysmextCommands = append(prysmextCommands, Commands...)
}
