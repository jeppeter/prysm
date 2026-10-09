package main

import (
	"fmt"
	"github.com/OffchainLabs/prysm/v7/cmd"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmctl/checkpointsync"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmctl/db"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmctl/p2p"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmctl/testnet"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmctl/validator"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmctl/weaksubjectivity"
	"github.com/sirupsen/logrus"
	"github.com/urfave/cli/v2"
	"io"
	"os"
)

var prysmctlCommands []*cli.Command
var prysmctlFlags = []cli.Flag{
	cmd.VerbosityFlag,
	cmd.LogfilesFlag,
	cmd.LogappendFlag,
}

func main() {
	app := &cli.App{
		Flags:    prysmctlFlags,
		Commands: prysmctlCommands,
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

			err = nil
			return
		},
	}
	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}

func init() {
	prysmctlCommands = append(prysmctlCommands, checkpointsync.Commands...)
	prysmctlCommands = append(prysmctlCommands, db.Commands...)
	prysmctlCommands = append(prysmctlCommands, p2p.Commands...)
	prysmctlCommands = append(prysmctlCommands, testnet.Commands...)
	prysmctlCommands = append(prysmctlCommands, weaksubjectivity.Commands...)
	prysmctlCommands = append(prysmctlCommands, validator.Commands...)
}
