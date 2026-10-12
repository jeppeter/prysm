package itercfg

import (
	"fmt"
	"github.com/urfave/cli/v2"
	"io"
	"os"
	"reflect"
)

var Commands = []*cli.Command{
	{
		Name:   "itercfg",
		Usage:  "iter config values",
		Action: itercfg_Handler,
	},
}

func format_tab(tab int) (outs string) {
	outs = ""
	for i := 0; i < tab; i += 1 {
		outs += "    "
	}
	return
}

func iter_command(writer io.Writer, ctx *cli.Context, cmd *cli.Command, tab int) {
	var outs string
	outs = format_tab(tab)
	outs += fmt.Sprintf("Command [%s]\n", cmd.Name)

	writer.Write([]byte(outs))
	for _, flg := range cmd.Flags {
		iter_flags(writer, ctx, flg, tab+1)
	}

	for _, subcmd := range cmd.Subcommands {
		iter_command(writer, ctx, subcmd, tab+1)
	}
	return
}

func iter_flags(writer io.Writer, ctx *cli.Context, flags cli.Flag, tab int) {
	var outs string
	var val interface{}
	var flgname string
	var types string

	flgname = flags.Names()[0]
	if ctx.IsSet(flgname) {
		val = ctx.Value(flgname)
		types = reflect.TypeOf(val).String()
		outs = format_tab(tab)
		outs += fmt.Sprintf("Flag %s.(%s) [%v]\n", flgname, types, val)
		writer.Write([]byte(outs))
	} else {
		outs = format_tab(tab)
		outs += fmt.Sprintf("Flag %s not set\n", flgname)
		writer.Write([]byte(outs))
	}

	return
}

func itercfg_Handler(ctx *cli.Context) (err error) {
	/*now first to get the command*/
	var outs string
	log.Debugf("format ctx.Command")
	iter_command(os.Stdout, ctx, ctx.Command, 0)

	//log.Infof("len Commands [%d]", len(ctx.App.Commands))
	for _, cmd := range ctx.App.Commands {
		iter_command(os.Stdout, ctx, cmd, 0)
	}

	for _, flg := range ctx.App.Flags {
		iter_flags(os.Stdout, ctx, flg, 0)
	}

	var cnt int
	cnt = ctx.Args().Len()
	outs = format_tab(0)
	outs += fmt.Sprintf("Args %d\n", cnt)
	os.Stdout.Write([]byte(outs))
	if cnt > 0 {
		outs = format_tab(1)
	}

	for i := 0; i < cnt; i += 1 {
		if i > 0 {
			outs += ","
		}
		outs += ctx.Args().Get(i)
	}
	if cnt > 0 {
		outs += "\n"
		os.Stdout.Write([]byte(outs))
	}

	err = nil
	return
}
