package proto_array

import (
	"fmt"
	"lmd-ghost/eth2/dag"
	"log"
)

const nonExistentNode = ^uint64(0)

type ProtoArrayLMDGhost struct {
	dag *dag.BeaconDag

	// node best-child
	b []uint64
	// node values
	w []int64
	// node parents
	p []uint64
	// node best-targets
	t []uint64

	// nodes in order
	nodes []*dag.DagNode

	// root -> node index
	indices  map[*dag.DagNode]uint64
	pruneidx uint64
	orphans  map[uint64]uint64
}

func format_tab(tab int) (rets string) {
	rets = ""
	for i := 0; i < tab; i += 1 {
		rets += "    "
	}
	return
}

func (pa *ProtoArrayLMDGhost) PrintIdx(idx uint64) (outs string) {
	if idx == nonExistentNode {
		outs = "nonExistentNode"
	} else {
		outs = fmt.Sprintf("%d", idx+pa.pruneidx)
	}
	return
}

func (pa *ProtoArrayLMDGhost) PrintChild(chldmap map[uint64][]uint64, cur uint64, tab int) (outs string) {
	outs = ""
	pa.orphans[cur] = 1
	if len(pa.nodes) <= int(cur) {
		return
	}
	outs += format_tab(tab)
	outs += fmt.Sprintf("[%s]%s bestchild %s weight %d besttarget %s\n", pa.PrintIdx(cur), pa.nodes[cur].String(), pa.PrintIdx(pa.b[cur]), pa.w[cur], pa.PrintIdx(pa.t[cur]))
	chldren, ok := chldmap[cur]
	if !ok {
		return
	}
	for _, curch := range chldren {
		outs += pa.PrintChild(chldmap, curch, tab+1)
	}
	return
}

func (pa *ProtoArrayLMDGhost) PrintMap() (rets string) {
	rets = ""
	chs := make(map[uint64][]uint64)
	pa.orphans = make(map[uint64]uint64)
	for ii, i := range pa.p {
		if i != nonExistentNode {
			_, ok := chs[i]
			if !ok {
				chs[i] = []uint64{}
			}
			chs[i] = append(chs[i], uint64(ii))
		}
	}
	/*now we should give the */
	rets += pa.PrintChild(chs, 0, 0)

	for ci := 0; ci < len(pa.nodes); ci += 1 {
		_, ok := pa.orphans[uint64(ci)]
		if !ok {
			rets += fmt.Sprintf("orphan[%s]%s bestchild %s weight %d besttarget %s\n", pa.PrintIdx(uint64(ci)), pa.nodes[uint64(ci)].String(), pa.PrintIdx(pa.b[uint64(ci)]), pa.w[uint64(ci)], pa.PrintIdx(pa.t[uint64(ci)]))
		}
	}

	return
}

func NewProtoArrayLMDGhost(d *dag.BeaconDag) dag.ForkChoice {
	res := &ProtoArrayLMDGhost{
		dag:      d,
		indices:  make(map[*dag.DagNode]uint64),
		pruneidx: 0,
	}
	return res
}

func (gh *ProtoArrayLMDGhost) ApplyScoreChanges(changes []dag.ScoreChange) {
	// diff values: we map changes into an array mirroring the current state arrays.
	// These diff values can be propagated first, and then applied to the weights after.
	// This makes it easy to recognize when a "change" cancels out somewhere:
	//  the diff value will be 0, just like any non-change.

	log.Printf("Start ApplyScoreChanges len(%d)\n", len(changes))
	d := make([]int64, len(gh.nodes), len(gh.nodes))
	start := int64(gh.indices[gh.dag.Finalized])
	var pp *dag.DagNode
	var cnode *dag.DagNode
	for _, c := range changes {
		i := gh.indices[c.Target]
		log.Printf("d[%d][%s] 0x%x => 0x%x\n", i, c.Target.Key.String(), d[i], d[i]+c.ScoreDelta)
		d[i] += c.ScoreDelta
	}
	// back-prop diff values
	for i := int64(len(d)) - 1; i >= start; i-- {
		pi := gh.p[i]
		if pi == nonExistentNode {
			continue
		}
		if pi != 0 {
			cnode = gh.nodes[pi]
			pp = gh.nodes[i]
			log.Printf("d[%d][%s] 0x%x => 0x%x (d[%d][%s])\n", pi, cnode.Key.String(), d[pi], d[pi]+d[i], i, pp.Key.String())
			d[pi] += d[i]
		}
	}
	// apply diffs to weights
	// (note: array ADD, doesn't have to be a loop)
	for i, v := range d {
		if v != 0 {
			pp = gh.nodes[i]
			log.Printf("w[%d][%s] 0x%x => 0x%x [v 0x%x]\n", i, pp.Key.String(), gh.w[i], gh.w[i]+v, v)
			gh.w[i] += v
		}
	}
	// back-prop best-child/target updates
	for i := int64(len(d)) - 1; i >= start; i-- {
		// propagate best-target
		if bi := gh.b[i]; bi != nonExistentNode {
			pp = gh.nodes[i]
			cnode = gh.nodes[bi]
			log.Printf("t[%d][%s] 0x%x => 0x%x (t[%d][%s])\n", i, pp.Key.String(), gh.t[i], gh.t[bi], bi, cnode.Key.String())
			gh.t[i] = gh.t[bi]
		}
		// if this note did not change at all, then skip it
		if d[i] == 0 {
			log.Printf("continue for [%s] d[%d] == 0\n", gh.nodes[i].Key.String(), i)
			continue
		}
		// parent of i (may not exist)
		pi := gh.p[i]
		if pi == nonExistentNode {
			log.Printf("continue parent for [%s] == nonExistentNode\n", gh.nodes[i].Key.String())
			continue
		}
		ui := uint64(i)
		// best child of the parent of i
		bpi := gh.b[pi]
		if bpi == nonExistentNode {
			// i is better than nothing, easy
			pp = gh.nodes[pi]
			log.Printf("b[%d][%s] 0x%x => 0x%x\n", pi, pp.Key.String(), gh.b[pi], ui)
			gh.b[pi] = ui
			continue
		}
		// if i is already the best, don't do any work
		// if i changed better than the bpi, then it's worth looking at.
		if bpi != ui && d[i] > d[bpi] {
			// now look at the weights: if i is better than bpi,
			// it becomes the best-child for its parent, and the parent is assigned the best-target of i
			if gh.w[i] > gh.w[bpi] {
				pp = gh.nodes[pi]
				log.Printf("b[%d][%s] 0x%x => 0x%x\n", pi, pp.Key.String(), gh.b[pi], ui)
				gh.b[pi] = ui
			}
		}
	}
	log.Printf("End ApplyScoreChanges\n")
	log.Printf("ApplyScoreChanges\n%s\n", gh.PrintMap())
}

func (gh *ProtoArrayLMDGhost) OnNewNode(block *dag.DagNode) {
	i := uint64(len(gh.nodes))
	gh.indices[block] = i
	// the new node does not have a best-child
	gh.b = append(gh.b, nonExistentNode)
	// new node is weighted 0
	gh.w = append(gh.w, 0)
	// the new node may not have a parent
	if block.Parent == nil {
		gh.p = append(gh.p, nonExistentNode)
	} else {
		// or the parent may be out of scope
		if pi, ok := gh.indices[block.Parent]; ok {
			gh.p = append(gh.p, pi)
			// if it is the first child, it is also the best.
			if gh.b[pi] == nonExistentNode {
				gh.b[pi] = i
			}
		} else {
			gh.p = append(gh.p, nonExistentNode)
		}
	}
	// new node points to itself as a best-target, since it is a leaf.
	gh.t = append(gh.t, i)
	gh.nodes = append(gh.nodes, block)
}

func (gh *ProtoArrayLMDGhost) OnPrune() {
	// get the index of the finalized node, and adjust to current array-space.
	start := gh.indices[gh.dag.Finalized]
	// Small pruning does not help more than it costs to do. Postpone pruning in such case.
	// For implementers: tune this parameter, or trigger pruning based on this value going over a threshold.
	if start < 200 {
		return
	}
	log.Printf("OnPrune %d\n", start)
	// Note: the elements pruned at the start will stay in the backing array.
	// However, since we are appending to the slice, append() may re-allocate
	// the slice to a new backing array: eventually the pruned parts will be GC'd.
	gh.b = gh.b[start:]
	gh.w = gh.w[start:]
	gh.p = gh.p[start:]
	gh.t = gh.t[start:]

	// now delete all pruned nodes from the key->index lookup-map.
	for i := uint64(0); i < start; i++ {
		n := gh.nodes[i]
		delete(gh.indices, n)
	}
	gh.nodes = gh.nodes[start:]

	// adjust indices back to 0
	for i, n := range gh.nodes {
		// best-child may not exist, i.e. does not need to be adjusted
		if gh.b[i] != nonExistentNode {
			gh.b[i] -= start
		}
		gh.t[i] -= start
		// parent may not exist anymore
		if gh.p[i] < start {
			gh.p[i] = nonExistentNode
		} else {
			gh.p[i] -= start
		}
		gh.indices[n] -= start
	}
	/*to make prune as ok*/
	gh.pruneidx += start
	log.Printf("OnPrune %d\n", gh.pruneidx)
}

func (gh *ProtoArrayLMDGhost) HeadFn() *dag.DagNode {
	// look up the index of the finalized node, this is our starting point
	i := gh.indices[gh.dag.Finalized]
	oi := i
	for {
		if bi := gh.b[i]; bi != nonExistentNode {
			log.Printf("new HeadFn %s\n", gh.nodes[bi].String())
			i = bi
		} else {
			break
		}
	}
	if oi != i {
		log.Printf("new HeadFn final %s\n", gh.nodes[i].String())
	}
	// Get the target (again, adjust index)
	log.Printf("HeadFn\n%s\n", gh.PrintMap())
	return gh.nodes[i]
}
