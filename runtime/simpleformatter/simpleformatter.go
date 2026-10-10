package simpleformatter

import (
	"fmt"
	"github.com/sirupsen/logrus"
	"time"
)

type SimpleFormatter struct {
	DebugFileLine bool
	TimeFormat    bool
	LevelFormat   bool
	PackageFormat bool
}

func NewSimpleFormatter() (retp *SimpleFormatter, err error) {
	err = nil
	retp = &SimpleFormatter{
		DebugFileLine: false,
		TimeFormat:    false,
		LevelFormat:   true,
		PackageFormat: true,
	}
	return
}

func (f *SimpleFormatter) Format(entry *logrus.Entry) (outb []byte, err error) {
	var outs string = ""
	if f.LevelFormat {
		switch entry.Level {
		case logrus.DebugLevel:
			outs += "<debug>"
		case logrus.TraceLevel:
			outs += "<trace> "
		case logrus.WarnLevel:
			outs += "<warn>"
		case logrus.ErrorLevel:
			outs += "<error>"
		case logrus.FatalLevel:
			outs += "<fatal>"
		case logrus.PanicLevel:
			outs += "<panic>"
		case logrus.InfoLevel:
			outs += "<info>"
		default:
			outs += "<unknown level>"
		}

		outs += " "
	}

	if f.PackageFormat {
		var s string
		var ok bool
		s, ok = entry.Data["package"].(string)
		if ok {
			outs += fmt.Sprintf("package[%s] ", s)
		}
	}

	if f.DebugFileLine {
		if entry.HasCaller() {
			outs += fmt.Sprintf("[%s:%d] ", entry.Caller.File, entry.Caller.Line)
		}
	}
	if f.TimeFormat {
		outs += fmt.Sprintf("[%s] ", entry.Time.Format(time.RFC3339))
	}

	outs += fmt.Sprintf("%s\n", entry.Message)
	outb = []byte(outs)
	err = nil
	return
}
