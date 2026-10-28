package dag

import "lmd-ghost/eth2/common"
import "fmt"

type DagNode struct {
	Parent *DagNode

	Children []*DagNode

	// note: it's preferred to just use the pointer to this node as a key wherever possible.
	// The key can still be used to make super-keys (here: concatenation of keys) etc. for caching and other optimizations.
	Key common.Hash256

	// Unused in DAG processing, but useful for debugging / checking simulation
	Proposer common.ValidatorID

	Slot uint64

	// Raw height, a.k.a. distance from genesis in number of blocks. Not used in every implementation.
	Height uint64

	// Note: unused in most algorithms. Most algorithms keep track of scores with a map of latest-scores,
	//  and optimized access to this map from another point in the graph.
	Weight int64

	// Unused in some implementations
	BestTarget *DagNode

	// Unused in some implementations
	IndexAsChild uint32
}

func (d *DagNode) String() string {
	var rets string
	rets = ""
	rets += fmt.Sprintf("DagNode[Key %s Slot 0x%x Height 0x%x Weight 0x%x Proposer 0x%x", d.Key.String(), d.Slot, d.Height, d.Weight, d.Proposer)
	if d.Parent != nil {
		rets += fmt.Sprintf(" Parent.Key %s", d.Parent.Key.String())
	}
	rets += "]"
	return rets
}
