package main

import (
	"os"

	"github.com/OffchainLabs/prysm/v7/cmd/prysmext/checkenv"
	"github.com/urfave/cli/v2"
)

var prysmextCommands []*cli.Command

func main() {
	app := &cli.App{
		Commands: prysmextCommands,
	}
	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}

func init() {
	prysmextCommands = append(prysmextCommands, checkenv.Commands...)
}
