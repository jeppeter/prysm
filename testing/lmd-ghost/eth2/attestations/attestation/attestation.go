package attestation

import "lmd-ghost/eth2/common"
import "fmt"

type Attestation struct {
	BeaconBlockRoot common.Hash256

	Attester common.ValidatorID

	Weight uint64
}

func (ats *Attestation) String() (rets string) {
	rets = ""
	rets += fmt.Sprintf("Attestation[BeaconBlockRoot %s ValidatorID 0x%x Weight 0x%x]", ats.BeaconBlockRoot.String(), ats.Attester, ats.Weight)
	return
}
