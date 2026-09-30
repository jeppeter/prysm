package checkenv

import "github.com/urfave/cli/v2"
import "github.com/herumi/bls-eth-go-binary/bls"

var Commands = []*cli.Command{
	{
		Name:    "checkenv",
		Aliases: []string{"chkenv"},
		Usage:   "commands for check environment for compile",
		Action:  checkenv_Handler,
	},
}

func checkenv_Handler(ctx *cli.Context) (err error) {
	if err = bls.Init(bls.BLS12_381); err != nil {
		return
	}
	if err = bls.SetETHmode(bls.EthModeDraft07); err != nil {
		return
	}
	// Check subgroup order for pubkeys and signatures.
	bls.VerifyPublicKeyOrder(true)
	bls.VerifySignatureOrder(true)
	err = nil
	return
}
