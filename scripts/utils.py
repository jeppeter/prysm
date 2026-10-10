#! /usr/bin/env python


import os
import extargsparse
import sys
import traceback
import re
import logging
import subprocess
import cmdpack
import json
import signal
import time
import shutil

sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__))))

from loglib import set_logging, load_log_commandline,log_command_prefix
from fileop import read_file,write_file,make_directory_safe,mktemp_file
from envop import is_windows,is_linux
from tomlex import TomlEx
from strop import rand_buffer
from procop import ProcExpolore


class ArgsForge(object):
    def __init__(self,content=None):
        self.topdir = None
        self.datadir = None
        self.gethdir = None
        self.gethdatadir = None
        self.goos = None
        self.goarch = None
        self.goproxy = None
        self.force = False
        self.chainconfigfile = None
        if not (content is  None):
            rdict = json.loads(content)
            for (k,v) in rdict:
                if k == 'topdir':
                    self.topdir = v
                elif k == 'datadir':
                    self.datadir = v
                elif k == 'gethdir':
                    self.gethdir = v
                elif k == 'gethdatadir':
                    self.gethdatadir = v
                elif k == 'force':
                    self.force = v
                elif k == 'goos':
                    self.goos = v
                elif k == 'goarch':
                    self.goarch = v
                elif k == 'goproxy':
                    self.goproxy = v
                elif k == 'chainconfigfile':
                    self.chainconfigfile = v
        if self.topdir is None:
            self.topdir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
        if self.datadir is None:
            if is_windows():
                self.datadir = os.path.join(self.topdir,'datadir_windows')
            else:
                self.datadir = os.path.join(self.topdir,'datadir_linux')
        if self.gethdir is None:
            self.gethdir = os.path.abspath(os.path.join(self.topdir,'..','go-ethereum'))
        if self.gethdatadir is None:
            if is_windows():
                self.gethdatadir = os.path.join(self.gethdir,'datastore_windows')
            else:
                self.gethdatadir = os.path.join(self.gethdir,'datastore_linux')
        if self.chainconfigfile is None:
            self.chainconfigfile = os.path.join(self.topdir,'scripts','config.yml')
        if self.goproxy is None:
            self.goproxy = 'https://goproxy.cn'
        return
            

def get_support_bin(topdir):
    cmddir = os.path.join(topdir,'cmd')
    dirs = os.listdir(cmddir)
    retdirs = []
    for d in dirs:
        curd = os.path.join(cmddir,d)
        if os.path.isdir(curd):
            curf = os.path.join(curd,'main.go')
            if os.path.isfile(curf):
                retdirs.append(d)
    return retdirs

def get_go_cmd():
    if is_windows():
        return 'go.exe'
    else:
        return 'go'

def get_extbin(args):
    retval = os.path.join(args.topdir,'cmd','prysmext','prysmext')
    if is_windows():
        retval += '.exe'
    return retval

def get_prysm_bin(args,n):
    retval = os.path.join(args.topdir,'cmd',n,n)
    if is_windows():
        retval += '.exe'
    return retval

def compile_bin(args,d):
    outf = os.path.join(args.topdir,'cmd',d,d)
    if is_windows():
        outf += '.exe'
    if os.path.isfile(outf) and not args.force:
        return True
    curdir = os.getcwd()
    retval = False
    try:
        myenv= os.environ.copy()
        myenv['CGO_CFLAGS'] = '-O -D__BLST_PORTABLE__'
        myenv['GOPROXY'] = args.goproxy
        if args.goos is not None:
            myenv['GOOS'] = args.goos
        if args.goarch is not None:
            myenv['GOARCH'] = args.goarch
        os.chdir(args.topdir)
        cmds = []
        cmds.append(get_go_cmd())
        cmds.append('build')
        cmds.append('-o')
        if is_windows():
            outf = '.\\cmd\\%s\\%s.exe'%(d,d)
            cmds.append(outf)
            cmds.append('.\\cmd\\%s'%(d))
        else:
            outf = './cmd/%s/%s'%(d,d)
            cmds.append(outf)
            cmds.append('./cmd/%s'%(d))
        subprocess.check_call(cmds,env=myenv)
        retval = True
    except:
        logging.error('%s'%(traceback.format_exc()))
    os.chdir(curdir)
    return retval

def compile_handler(args,parser):
    set_logging(args)
    supportbins = get_support_bin(args.topdir)
    for d in args.subnargs:
        if d not in supportbins:
            sys.stderr.write('%s not in support %s bins\n'%(d,args.topdir))
            sys.exit(3)
        retval = compile_bin(args,d)
        if not retval:
            sys.stderr.write('can not compile %s\n'%(d))
            sys.exit(3)
    sys.exit(0)
    return

def checkenv_handler(args,parser):
    set_logging(args)
    retval = compile_bin(args,'prysmext')
    if not retval:
        raise Exception('can not compile prysmext')
    cmds = [get_extbin(args)]
    cmds.append('checkenv')
    try:
        logging.info('cmds %s'%(cmds))
        subprocess.check_call(cmds)
        sys.stdout.write('compile environment ok\n')
    except:
        logging.error('%s'%(traceback.format_exc()))
        sys.exit(3)
    sys.exit(0)
    return


def get_forkname(args=None):
    if args is None:
        args = ArgsForge()
    # now first to compile the 
    retval = compile_bin(args,'prysmext')
    if not retval:
        raise Exception('can not run compile prysmext')
    cmds = [get_extbin(args)]
    cmds.append('expforkname')
    po = subprocess.run(cmds,capture_output=True)
    try:
        po.check_returncode()
    except:
        sys.stderr.write('run %s error\n%s'%(cmds,traceback.format_exc()))
        raise Exception('%s erorr'%(cmds))
    outb = po.stdout    
    try:
        outs = outb.decode('utf-8')
        rarr = json.loads(outs)
    except:
        raise Exception('output %s error\n%s'%(outb,traceback.format_exc()))
    return rarr

def unescape_handler(args,parser):
    set_logging(args)
    ins = read_file(args.input)
    outs = ins.replace('\\n','\n')
    write_file(outs,args.output)
    sys.exit(0)

def find_geth_genesis(args):
    allfiles = os.listdir(args.gethdatadir)
    genexpr = re.compile('genesis\\.([^\\.]+)\\.json')
    retfile = None
    for f in allfiles:
        if genexpr.match(f):
            curf = os.path.join(args.gethdatadir,f)
            if os.path.isfile(curf):
                retfile = curf
                break
    return retfile

KEYWORD_ALLOC = 'alloc'

def generate_genesis(args,prysmctl,genin):
    ins = read_file(genin)
    retval = False
    make_directory_safe(args.datadir)
    logfile = os.path.join(args.datadir,'ssz.log')
    rdict =json.loads(ins)
    validators = 0
    if KEYWORD_ALLOC in rdict.keys():
        cdict = rdict[KEYWORD_ALLOC]
        validators = len(cdict.keys())
    if validators < 2:
        raise Exception('validators %d < 2'%(validators))
    genout = os.path.join(args.datadir,'genesis.out.json')
    genssz = os.path.join(args.datadir,'genesis.ssz')
    cmds = [prysmctl]
    cmds.append('--verbosity')
    cmds.append('trace')
    cmds.append('--log-format')
    cmds.append('simple')
    cmds.append('--log.files=%s'%(logfile))
    cmds.append('testnet')
    cmds.append('generate-genesis')
    cmds.append('--fork=%s'%(args.forkname))
    cmds.append('--num-validators=%d'%(validators))
    cmds.append('--chain-config-file=%s'%(args.chainconfigfile))
    cmds.append('--geth-genesis-json-in=%s'%(genin))
    cmds.append('--output-ssz=%s'%(genssz))
    cmds.append('--geth-genesis-json-out=%s'%(genout))
    try:
        logging.info('cmds %s'%(cmds))
        ndevnull = open(os.devnull,'w+')
        subprocess.check_call(cmds,stdout=ndevnull,stderr=ndevnull)
        retval = True
    except:
        retval = False
        logging.error('%s'%(traceback.format_exc()))

    return retval

def genssz_handler(args,parser):
    set_logging(args)
    # now first to find the genesis in
    genin = find_geth_genesis(args)
    if genin is None:
        raise Exception('can not find genesis.json in %s'%(args.gethdatadir))
    prysmctl = get_prysm_bin(args,'prysmctl')
    if not os.path.isfile(prysmctl):
        raise Exception('no %s compiled'%(prysmctl))
    # now we should give the genesis
    forknames = get_forkname(args)
    if args.forkname not in forknames:
        raise Exception('%s fork not support'%(args.forkname))

    retval = generate_genesis(args,prysmctl,genin)
    if not retval:
        sys.exit(3)
    sys.exit(0)

def load_base_parser(parser):
    commandline_fmt='''
    {
        "input|i" : null,
        "output|o" : null,
        "goproxy" : "https://goproxy.cn",
        "go111module" : "auto",
        "goos" : null,
        "goarch" : null,
        "rpcpipe" : null,
        "reserved|R" : false,
        "networkid" : 2363,
        "topdir" : "%s",
        "datadir" : "%s",
        "gethdir" : "%s",
        "gethdatadir" : "%s",
        "chainconfigfile" : "%s",
        "force|F" : false,
        "forkname##forkname for pos specified support is %s##" : "%s",
        "compile<%s.compile_handler>##bins ... to compile bins now support is %s ##" : {
            "$" : "+"
        },
        "checkenv<%s.checkenv_handler>##to check environment to compile##" : {
            "$" : 0
        },
        "unescape<%s.unescape_handler>##to unescape for file##" : {
            "$" : 0
        },
        "genssz<%s.genssz_handler>##to make genesis ssz##" : {
            "$" : 0
        }
    }
    '''
    args = ArgsForge()
    support_binnames = get_support_bin(args.topdir)
    support_bin_dir = ''
    for d in support_binnames:
        if len(support_bin_dir) > 0:
            support_bin_dir += ','
        support_bin_dir += '%s'%(d)
    repltopdir = args.topdir
    replgethdir = args.gethdir
    repldatadir = args.datadir
    replgethdatadir = args.gethdatadir
    replchainconfigfile = args.chainconfigfile

    if is_windows():
        repltopdir = repltopdir.replace('\\','\\\\')
        replgethdir = replgethdir.replace('\\','\\\\')
        repldatadir = repldatadir.replace('\\','\\\\')
        replgethdatadir = replgethdatadir.replace('\\','\\\\')
        replchainconfigfile = replchainconfigfile.replace('\\','\\\\')
    forknames = get_forkname(args)
    forks = ''
    deffork = ''
    if len(forknames) > 0:
        deffork = forknames[0]
    for v in forknames:
        if len(forks) > 0:
            forks += ','
        forks += v

    commandline = commandline_fmt%(repltopdir,repldatadir,replgethdir,replgethdatadir,replchainconfigfile,forks,deffork,__name__,support_bin_dir,__name__,__name__,__name__)
    parser.load_command_line_string(commandline)
    return parser


def main():
    parser = extargsparse.ExtArgsParse()
    load_log_commandline(parser)
    load_base_parser(parser)
    parser.parse_command_line(None,parser)
    raise Exception('can not here for no command handle')
    return


if __name__ == '__main__':
    main()	