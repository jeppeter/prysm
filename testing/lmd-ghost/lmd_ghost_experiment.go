package main

import (
	"encoding/json"
	"fmt"
	"lmd-ghost/sim"
	"log"
	"os"
	"time"
)

func main() {
	config := &sim.SimConfig{
		ValidatorCount:       3,
		LatencyFactor:        0.8,
		SlotSkipChance:       0.3,
		BaseAttestWeight:     100,
		MaxExtraAttestWeight: 10,
		Blocks:               500,
		AttestationsPerBlock: 10,
		JustifyEpochsAgo:     2,
		FinalizeEpochsAgo:    3,
		ForkChoiceRule:       "proto_array",
	}
	var err error

	if len(os.Args) > 1 {
		if os.Args[1] == "-h" || os.Args[1] == "--help" {
			fmt.Fprintf(os.Stderr, "%s [logfile] [jsonfile]\n", os.Args[0])
			return
		}

		var ofile *os.File = nil
		_, err = os.Stat(os.Args[1])
		if err != nil {
			ofile, err = os.Create(os.Args[1])
		} else {
			ofile, err = os.OpenFile(os.Args[1], os.O_WRONLY, 0666)
		}
		if err != nil {
			panic(fmt.Sprintf("open [%s] error %s", os.Args[1], err.Error()))
		}
		log.SetOutput(ofile)
	}

	log.SetFlags(log.Llongfile | log.Ldate | log.Ltime | log.Lmicroseconds)

	if len(os.Args) > 2 {
		var inb []byte
		inb, err = os.ReadFile(os.Args[2])
		if err != nil {
			panic(fmt.Sprintf("read [%s] error %s", os.Args[2], err.Error()))
		}
		err = json.Unmarshal(inb, config)
		if err != nil {
			panic(fmt.Sprintf("parse [%s] error %s", os.Args[2], err.Error()))
		}
	}

	s := sim.NewSimulation(config)
	name := config.String()

	log.Println("Start:	", name)
	startTime := time.Now()
	s.RunSim()
	endTime := time.Now()
	log.Println("End: ", name, "took", endTime.Sub(startTime))

	// Optional: write the network graph of the chain to a nodes and edges CSV
	// s.SaveNetworkGraph()

}
