package itercfg

import (
	"fmt"
	"github.com/OffchainLabs/prysm/v7/cmd"
	"github.com/urfave/cli/v2"
	"os"
	"strings"
)

var Commands = []*cli.Command{
	{
		Name:   "itercfg",
		Usage:  "iter config values",
		Action: itercfg_Handler,
	},
}

func itercfg_Handler(ctx *cli.Context) (err error) {
	/*now first to get the command*/
	var outs string
	var owriter strings.Builder

	err = cmd.IterContext(ctx, &owriter)
	outs = owriter.String()
	fmt.Fprintf(os.Stdout, "%s", outs)

	err = nil
	return
}
