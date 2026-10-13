package cmd

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"path"
	"reflect"
	"runtime"
	"strings"

	"github.com/OffchainLabs/prysm/v7/io/file"
	"github.com/pkg/errors"
	"github.com/sirupsen/logrus"
	"github.com/urfave/cli/v2"
)

// ConfirmAction uses the passed in actionText as the confirmation text displayed in the terminal.
// The user must enter Y or N to indicate whether they confirm the action detailed in the warning text.
// Returns a boolean representing the user's answer.
func ConfirmAction(actionText, deniedText string) (bool, error) {
	var confirmed bool
	reader := bufio.NewReader(os.Stdin)
	log.Warn(actionText)

	for {
		fmt.Print(">> ")

		line, _, err := reader.ReadLine()
		if err != nil {
			return false, err
		}
		trimmedLine := strings.TrimSpace(string(line))
		lineInput := strings.ToUpper(trimmedLine)
		if lineInput != "Y" && lineInput != "N" {
			log.Errorf("Invalid option of %s chosen, please only enter Y/N", line)
			continue
		}
		if lineInput == "Y" {
			confirmed = true
			break
		}
		log.Warn(deniedText)
		break
	}

	return confirmed, nil
}

// ExpandSingleEndpointIfFile expands the path for --execution-provider if specified as a file.
func ExpandSingleEndpointIfFile(ctx *cli.Context, flag *cli.StringFlag) error {
	// Return early if no flag value is set.
	if !ctx.IsSet(flag.Name) {
		return nil
	}
	// Return early for non-unix operating systems, as there is
	// no shell path expansion for ipc endpoints on windows.
	if runtime.GOOS == "windows" {
		return nil
	}
	web3endpoint := ctx.String(flag.Name)
	switch {
	case strings.HasPrefix(web3endpoint, "http://"):
	case strings.HasPrefix(web3endpoint, "https://"):
	case strings.HasPrefix(web3endpoint, "ws://"):
	case strings.HasPrefix(web3endpoint, "wss://"):
	default:
		web3endpoint, err := file.ExpandPath(ctx.String(flag.Name))
		if err != nil {
			return errors.Wrapf(err, "could not expand path for %s", ctx.String(flag.Name))
		}
		if err := ctx.Set(flag.Name, web3endpoint); err != nil {
			return errors.Wrapf(err, "could not set %s to %s", flag.Name, web3endpoint)
		}
	}
	return nil
}

// ParseVModule parses a comma-separated list of package=level entries.
func ParseVModule(input string) (map[string]logrus.Level, logrus.Level, error) {
	var l logrus.Level
	trimmed := strings.TrimSpace(input)
	if trimmed == "" {
		return nil, l, nil
	}

	parts := strings.Split(trimmed, ",")
	result := make(map[string]logrus.Level, len(parts))
	for _, raw := range parts {
		entry := strings.TrimSpace(raw)
		if entry == "" {
			return nil, l, fmt.Errorf("invalid vmodule entry: empty segment")
		}
		kv := strings.Split(entry, "=")
		if len(kv) != 2 {
			return nil, l, fmt.Errorf("invalid vmodule entry %q: expected path=level", entry)
		}
		pkg := strings.TrimSpace(kv[0])
		levelText := strings.TrimSpace(kv[1])
		if pkg == "" {
			return nil, l, fmt.Errorf("invalid vmodule entry %q: empty package path", entry)
		}
		if levelText == "" {
			return nil, l, fmt.Errorf("invalid vmodule entry %q: empty level", entry)
		}
		if strings.Contains(pkg, "*") {
			return nil, l, fmt.Errorf("invalid vmodule package path %q: wildcards are not allowed", pkg)
		}
		if strings.ContainsAny(pkg, " \t\n") {
			return nil, l, fmt.Errorf("invalid vmodule package path %q: whitespace is not allowed", pkg)
		}
		if strings.HasPrefix(pkg, "/") {
			return nil, l, fmt.Errorf("invalid vmodule package path %q: leading slash is not allowed", pkg)
		}
		cleaned := path.Clean(pkg)
		if cleaned != pkg || pkg == "." || pkg == ".." {
			return nil, l, fmt.Errorf("invalid vmodule package path %q: must be an absolute package path. (trailing slash not allowed)", pkg)
		}
		if _, exists := result[pkg]; exists {
			return nil, l, fmt.Errorf("invalid vmodule package path %q: duplicate entry", pkg)
		}
		level, err := logrus.ParseLevel(levelText)
		if err != nil {
			return nil, l, fmt.Errorf("invalid vmodule level %q: must be one of panic, fatal, error, warn, info, debug, trace", levelText)
		}
		result[pkg] = level
	}

	maxLevel := logrus.PanicLevel
	for _, lvl := range result {
		if lvl > maxLevel {
			maxLevel = lvl
		}
	}

	return result, maxLevel, nil
}

func FormatTab(tab int) (outs string) {
	outs = ""
	for i := 0; i < tab; i += 1 {
		outs += "    "
	}
	return
}

func IterCommand(writer io.Writer, ctx *cli.Context, cmd *cli.Command, tab int) (err error) {
	var outs string
	outs = FormatTab(tab)
	outs += fmt.Sprintf("Command [%s]\n", cmd.Name)

	writer.Write([]byte(outs))
	for _, flg := range cmd.Flags {
		err = IterFlags(writer, ctx, flg, tab+1)
		if err != nil {
			return
		}
	}

	for _, subcmd := range cmd.Subcommands {
		err = IterCommand(writer, ctx, subcmd, tab+1)
		if err != nil {
			return
		}
	}
	err = nil
	return
}

func IterFlags(writer io.Writer, ctx *cli.Context, flags cli.Flag, tab int) (err error) {
	var outs string
	var val interface{}
	var flgname string
	var types string

	flgname = flags.Names()[0]
	if ctx.IsSet(flgname) {
		val = ctx.Value(flgname)
		types = reflect.TypeOf(val).String()
		outs = FormatTab(tab)
		outs += fmt.Sprintf("Flag %s.(%s) [%v]\n", flgname, types, val)
		writer.Write([]byte(outs))
	} else {
		outs = FormatTab(tab)
		outs += fmt.Sprintf("Flag %s not set\n", flgname)
		writer.Write([]byte(outs))
	}
	err = nil
	return
}

func IterContext(ctx *cli.Context, owriter io.Writer) (err error) {
	err = IterCommand(owriter, ctx, ctx.Command, 0)
	if err != nil {
		return
	}

	for _, cmd := range ctx.App.Commands {
		err = IterCommand(owriter, ctx, cmd, 0)
		if err != nil {
			return
		}
	}

	for _, flg := range ctx.App.Flags {
		err = IterFlags(owriter, ctx, flg, 0)
		if err != nil {
			return
		}
	}

	var cnt int
	var outs string
	cnt = ctx.Args().Len()
	outs = FormatTab(0)
	outs += fmt.Sprintf("Args %d\n", cnt)
	owriter.Write([]byte(outs))
	if cnt > 0 {
		outs = FormatTab(1)
	}

	for i := 0; i < cnt; i += 1 {
		if i > 0 {
			outs += ","
		}
		outs += ctx.Args().Get(i)
	}
	if cnt > 0 {
		outs += "\n"
		owriter.Write([]byte(outs))
	}
	err = nil
	return
}
