package cmd

import (
	"fmt"
	"github.com/OffchainLabs/prysm/v7/io/logs"
	"github.com/OffchainLabs/prysm/v7/monitoring/journald"
	prefixed "github.com/OffchainLabs/prysm/v7/runtime/logging/logrus-prefixed-formatter"
	"github.com/OffchainLabs/prysm/v7/runtime/simpleformatter"
	joonix "github.com/joonix/log"
	"github.com/pkg/errors"
	"github.com/sirupsen/logrus"
	"github.com/urfave/cli/v2"
	"io"
	"os"
	"strings"
)

func LoadLogFlags(ctx *cli.Context, flags []cli.Flag, loadflags bool) (err error) {
	var formatter *simpleformatter.SimpleFormatter = &simpleformatter.SimpleFormatter{}
	formatter.DebugFileLine = false
	formatter.TimeFormat = false
	formatter.LevelFormat = true
	formatter.PackageFormat = false
	// Load flags from config file, if specified.
	if loadflags {
		if err = LoadFlagsFromConfig(ctx, flags); err != nil {
			return errors.Wrap(err, "failed to load flags from config file")
		}
	}

	// determine default log verbosity
	verbosity := ctx.String(VerbosityFlag.Name)
	if verbosity == "trace" || verbosity == "info" || verbosity == "warn" {
		formatter.DebugFileLine = true
		formatter.PackageFormat = true
		formatter.TimeFormat = true
		logrus.SetReportCaller(true)
	}

	verbosityLevel, err := logrus.ParseLevel(verbosity)
	if err != nil {
		return errors.Wrap(err, "failed to parse log verbosity")
	}

	// determine per package verbosity. if not set, maxLevel will be 0.
	vmoduleInput := strings.Join(ctx.StringSlice(LogVModuleFlag.Name), ",")
	vmodule, maxLevel, err := ParseVModule(vmoduleInput)
	if err != nil {
		return errors.Wrap(err, "failed to parse log vmodule")
	}

	logfs := ctx.StringSlice(LogfilesFlag.Name)
	var outf []io.Writer = []io.Writer{os.Stderr}
	if len(logfs) > 0 {
		for _, n := range logfs {
			var curf *os.File
			curf, err = os.OpenFile(n, os.O_CREATE|os.O_WRONLY, 0644)
			if err != nil {
				return err
			}
			outf = append(outf, curf)
		}
	}

	logapps := ctx.StringSlice(LogappendFlag.Name)
	if len(logapps) > 0 {
		for _, n := range logapps {
			var curf *os.File
			curf, err = os.OpenFile(n, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
			if err != nil {
				return err
			}
			outf = append(outf, curf)
		}
	}

	logrus.SetOutput(io.MultiWriter(outf...))

	format := ctx.String(LogFormat.Name)
	switch format {
	case "text":
		// disabling logrus default output so we can control it via different hooks
		logrus.SetOutput(io.Discard)

		// create a custom formatter and hook for terminal output
		formatter := new(prefixed.TextFormatter)
		formatter.TimestampFormat = "2006-01-02 15:04:05.00"
		formatter.FullTimestamp = true
		formatter.ForceFormatting = true
		formatter.ForceColors = true
		formatter.DisableColors = ctx.Bool(DisableLogColor.Name)
		formatter.VModule = vmodule
		formatter.BaseVerbosity = verbosityLevel

		logrus.AddHook(&logs.WriterHook{
			Formatter:     formatter,
			Writer:        os.Stderr,
			AllowedLevels: logrus.AllLevels[:max(verbosityLevel, maxLevel)+1],
			Identifier:    logs.LogTargetUser,
		})
	case "fluentd":
		// disabling logrus default output so we can control it via hooks
		logrus.SetOutput(io.Discard)

		f := joonix.NewFormatter()
		if err = joonix.DisableTimestampFormat(f); err != nil {
			panic(err) // lint:nopanic -- This shouldn't happen, but crashing immediately at startup is OK.
		}

		logrus.AddHook(&logs.WriterHook{
			Formatter:     f,
			Writer:        os.Stderr,
			AllowedLevels: logrus.AllLevels[:verbosityLevel+1],
			Identifier:    logs.LogTargetUser,
		})
	case "json":
		// disabling logrus default output so we can control it via hooks
		logrus.SetOutput(io.Discard)
		logrus.AddHook(&logs.WriterHook{
			Formatter: &logrus.JSONFormatter{
				TimestampFormat: "2006-01-02 15:04:05.00",
			},
			Writer:        os.Stderr,
			AllowedLevels: logrus.AllLevels[:verbosityLevel+1],
			Identifier:    logs.LogTargetUser,
		})
	case "journald":
		if err = journald.Enable(verbosityLevel); err != nil {
			return err
		}
	case "simple":
		logrus.SetFormatter(formatter)
	default:
		return fmt.Errorf("unknown log format %s", format)
	}

	return nil

}
