package block

import (
	"fmt"
	"lmd-ghost/eth2/common"
)

type BeaconBlock struct {
	ParentHash common.Hash256

	Hash common.Hash256

	Proposer common.ValidatorID

	Slot uint64

	// Lots of other stuff from the spec could be added here.

}

func (b *BeaconBlock) String() (rets string) {
	rets = ""
	rets += fmt.Sprintf("BeaconBlock[ParentHash %s Hash %s Proposer 0x%x Slot 0x%x]", b.ParentHash.String(), b.Hash.String(), b.Proposer, b.Slot)
	return
}
