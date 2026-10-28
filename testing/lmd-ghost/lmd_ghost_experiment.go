package main

import (
	"lmd-ghost/sim"
	"log"
	"time"
)

func main() {
	config := &sim.SimConfig{
		ValidatorCount:       40,
		LatencyFactor:        0.8,
		SlotSkipChance:       0.3,
		BaseAttestWeight:     100,
		MaxExtraAttestWeight: 10,
		Blocks:               100,
		AttestationsPerBlock: 10,
		JustifyEpochsAgo:     2,
		FinalizeEpochsAgo:    3,
		ForkChoiceRule:       "proto_array",
	}

	log.SetFlags(log.Llongfile | log.Ldate | log.Ltime | log.Lmicroseconds)
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
