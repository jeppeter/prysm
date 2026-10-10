package main

import (
	"fmt"
	"github.com/OffchainLabs/prysm/v7/cmd"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmext/checkenv"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmext/expforkname"
	"github.com/OffchainLabs/prysm/v7/runtime/simpleformatter"
	"github.com/sirupsen/logrus"
	"github.com/urfave/cli/v2"
	"io"
	"os"
	"strconv"
)

var prysmextCommands []*cli.Command

var appFlags = []cli.Flag{
	cmd.VerbosityFlag,
	cmd.LogfilesFlag,
	cmd.LogappendFlag,
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
			var formatter *simpleformatter.SimpleFormatter = &simpleformatter.SimpleFormatter{}
			formatter.DebugFileLine = false
			formatter.TimeFormat = false
			formatter.LevelFormat = true
			formatter.PackageFormat = false
			if verbose == "trace" || verbose == "info" || verbose == "warn" {
				formatter.DebugFileLine = true
				formatter.PackageFormat = true
				formatter.TimeFormat = true
				logrus.SetReportCaller(true)
			}
			verboselevel, err := logrus.ParseLevel(verbose)
			if err != nil {
				return
			}
			logrus.SetLevel(verboselevel)
			logfs := ctx.StringSlice(cmd.LogfilesFlag.Name)
			var outf []io.Writer = []io.Writer{os.Stderr}
			if len(logfs) > 0 {
				for _, n := range logfs {
					var curf *os.File
					curf, err = os.OpenFile(n, os.O_CREATE|os.O_WRONLY, 0644)
					if err != nil {
						return
					}
					outf = append(outf, curf)
				}
			}

			logapps := ctx.StringSlice(cmd.LogappendFlag.Name)
			fmt.Fprintf(os.Stderr, "LogappendFlag %v\n", logapps)
			if len(logapps) > 0 {
				for _, n := range logapps {
					var curf *os.File
					curf, err = os.OpenFile(n, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
					if err != nil {
						return
					}
					outf = append(outf, curf)
				}
			}

			logrus.SetOutput(io.MultiWriter(outf...))
			logrus.SetFormatter(formatter)

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
	prysmextCommands = append(prysmextCommands, checkenv.Commands...)
	prysmextCommands = append(prysmextCommands, expforkname.Commands...)
	prysmextCommands = append(prysmextCommands, Commands...)
}
