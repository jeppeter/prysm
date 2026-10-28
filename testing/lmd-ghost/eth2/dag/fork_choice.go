package dag

import (
	"fmt"
)

type ScoreChange struct {
	Target     *DagNode
	ScoreDelta int64
}

func (retp *ScoreChange) String() (rets string) {
	rets = ""
	rets += fmt.Sprintf("ScoreChange[ Target %s ScoreDelta 0x%x]", retp.Target.String(), retp.ScoreDelta)
	return
}

type ForkChoice interface {
	OnNewNode(node *DagNode)
	ApplyScoreChanges(changes []ScoreChange)
	OnPrune()
	HeadFn() *DagNode
}

type InitForkChoice func(dag *BeaconDag) ForkChoice
