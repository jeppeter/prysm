package main

import (
	"github.com/OffchainLabs/prysm/v7/cmd"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmctl/checkpointsync"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmctl/db"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmctl/p2p"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmctl/testnet"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmctl/validator"
	"github.com/OffchainLabs/prysm/v7/cmd/prysmctl/weaksubjectivity"
	"github.com/urfave/cli/v2"
	"os"
)

var prysmctlCommands []*cli.Command
var prysmctlFlags = []cli.Flag{
	cmd.VerbosityFlag,
	cmd.LogfilesFlag,
	cmd.LogappendFlag,
	cmd.LogFormat,
}

func main() {
	app := &cli.App{
		Flags:    prysmctlFlags,
		Commands: prysmctlCommands,
		Before: func(ctx *cli.Context) (err error) {
			err = cmd.LoadLogFlags(ctx, prysmctlFlags, false)
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

func init() {
	prysmctlCommands = append(prysmctlCommands, checkpointsync.Commands...)
	prysmctlCommands = append(prysmctlCommands, db.Commands...)
	prysmctlCommands = append(prysmctlCommands, p2p.Commands...)
	prysmctlCommands = append(prysmctlCommands, testnet.Commands...)
	prysmctlCommands = append(prysmctlCommands, weaksubjectivity.Commands...)
	prysmctlCommands = append(prysmctlCommands, validator.Commands...)
}
