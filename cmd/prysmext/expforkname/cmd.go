package expforkname

import (
	"fmt"
	"github.com/OffchainLabs/prysm/v7/runtime/version"
	"github.com/urfave/cli/v2"
)

var Commands = []*cli.Command{
	{
		Name:    "expforkname",
		Aliases: []string{"expfork"},
		Usage:   "commands for export fork names",
		Action:  expforkname_Handler,
	},
}

func expforkname_Handler(ctx *cli.Context) (err error) {
	var outs string = "["

	for i, vi := range version.All() {
		if i > 0 {
			outs += ","
		}
		outs += fmt.Sprintf("\"%s\"", version.String(vi))
	}
	outs += "]"
	fmt.Printf("%s\n", outs)

	return
}
