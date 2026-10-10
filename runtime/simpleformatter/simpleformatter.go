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

	if f.DebugFileLine {
		if entry.HasCaller() {
			outs += fmt.Sprintf("[%s:%d] ", entry.Caller.File, entry.Caller.Line)
		}
	}
	if f.TimeFormat {
		outs += fmt.Sprintf("[%s] ", entry.Time.Format(time.RFC3339))
	}

	for k, v := range entry.Data {
		if k == logrus.FieldKeyMsg {
			continue
		}
		if k == logrus.FieldKeyTime {
			continue
		}
		if k == logrus.FieldKeyLevel {
			continue
		}

		if k == logrus.FieldKeyLogrusError {
			continue
		}

		if k == logrus.FieldKeyFunc {
			continue
		}

		if k == logrus.FieldKeyFile {
			continue
		}
		outs += fmt.Sprintf("%s[%v] ", k, v)
	}

	outs += fmt.Sprintf("%s\n", entry.Message)
	outb = []byte(outs)
	err = nil
	return
}
