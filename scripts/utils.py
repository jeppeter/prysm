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
import eth_utils

sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__))))

from loglib import set_logging, load_log_commandline,log_command_prefix
from fileop import read_file,write_file,make_directory_safe,mktemp_file
from envop import is_windows,is_linux
from tomlex import TomlEx
from strop import rand_buffer
from procop import ProcExpolore
from key_word import *
from yamlex import YamlEx


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

def geth_dir_file(args,username,partfile):
    retfile = os.path.join(args.gethdatadir,'datadir_%s'%(username),partfile)
    return retfile

def datadir_file(args,username,partfile):
    retfile = os.path.join(args.datadir,'datadir_%s'%(username),partfile)
    return retfile

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

def find_keystore_file(args,username):
    keydir = os.path.join(args.gethdatadir,'datadir_%s'%(username),'keystore')
    files = os.listdir(keydir)
    fileexpr = re.compile('^UTC-.*$')
    retval = None
    for f in files:
        if fileexpr.match(f):
            retval = os.path.join(keydir,f)
            break
    return retval


def make_address_checksum(addr_str):
    addr = eth_utils.to_bytes(hexstr=addr_str)
    hex_addr = addr.hex()
    checksummed_buffer = ""

    # Treat the hex address as ascii/utf-8 for keccak256 hashing
    hashed_address = eth_utils.keccak(text=hex_addr).hex()

    # Iterate over each character in the hex address
    for nibble_index, character in enumerate(hex_addr):

        if character in "0123456789":
            # We can't upper-case the decimal digits
            checksummed_buffer += character
        elif character in "abcdef":
            # Check if the corresponding hex digit (nibble) in the hash is 8 or higher
            hashed_address_nibble = int(hashed_address[nibble_index], 16)
            if hashed_address_nibble > 7:
                checksummed_buffer += character.upper()
            else:
                checksummed_buffer += character
        else:
            raise eth_utils.ValidationError(
                f"Unrecognized hex character {character!r} at position {nibble_index}"
            )

    return "0x" + checksummed_buffer


def make_beacon_config_file(args,username,rdict,startport):
    # first to get the toml file
    curport = startport
    tomlfile = geth_dir_file(args,username,'%s.toml'%(username))
    keyfile = find_keystore_file(args,username)
    if keyfile is None:
        raise Exception('can not find keystore file in %s'%(args.gethdatadir))
    keyins = read_file(keyfile)
    keydict = json.loads(keyins)
    if KEYSTORE_ADDRESS_KEYWORD not in keydict.keys():
        raise Exception('%s not in %s keystore file'%(KEYSTORE_ADDRESS_KEYWORD,keyfile))
    keyaddress = keydict[KEYSTORE_ADDRESS_KEYWORD]
    yamlfile = datadir_file(args,username,'beacon_config.yaml')
    chaincfgfile = datadir_file(args,username,'genesis_config.yaml')
    ydatadir = os.path.dirname(datadir_file(args,username,'empty'))
    logfile = datadir_file(args,username,'beacon_%s.log'%(username))
    make_directory_safe(ydatadir)
    ins = read_file(tomlfile)
    tex = TomlEx()
    tex.loads(ins)
    # now to get the values
    yex = YamlEx()
    jwtsec = tex.get_value(NODE_JWTSECRET_KEYWORD)
    if jwtsec is None:
        raise Exception('can not get %s in %s'%(NODE_JWTSECRET_KEYWORD,tomlfile))
    yex.set_value(YAML_JWTSECRET_KEYWORD,jwtsec)
    yex.set_value(YAML_DATADIR_KEYWORD,ydatadir)
    cnt = 0
    for k in rdict.keys():
        cnt += 1
    cnt += 1
    cnt = int(cnt / 2)
    yex.set_value(YAML_MINSYNCPEERS_KEYWORD,cnt)
    sszfile = datadir_file(args,username,'genesis.ssz')
    origfile = os.path.join(args.datadir,'genesis.ssz')
    shutil.copyfile(origfile,sszfile)
    yex.set_value(YAML_GENESIS_STATE_KEYWORD,sszfile)
    shutil.copyfile(args.chainconfigfile,chaincfgfile)
    yex.set_value(YAML_CHAIN_CONFIG_FILE_KEYWORD,chaincfgfile)
    yex.set_value(YAML_CONTRACT_DEPLOYMENT_BLOCK_KEYWORD,0)
    yex.set_value(YAML_CHAIN_ID_KEYWORD,args.networkid)
    yex.set_value(YAML_RPC_HOST_KEYWORD,'127.0.0.1')
    yex.set_value(YAML_RPC_PORT_KEYWORD,curport)
    curport += 1
    yex.set_value(YAML_GRPC_GATEWAY_HOST_KEYWORD,'127.0.0.1')
    yex.set_value(YAML_GRPC_GATEWAY_PORT_KEYWORD,curport)
    curport += 1
    authhost = tex.get_value(NODE_AUTHADDR_KEYWORD)
    authport = tex.get_value(NODE_AUTHPORT_KEYWORD)
    if authhost is None or authport is None:
        raise Exception('[%s] or [%s] not in %s'%(NODE_AUTHADDR_KEYWORD,NODE_AUTHPORT_KEYWORD,tomlfile))
    yex.set_value(YAML_EXECUTION_ENDPOINT_KEYWORD,'http://%s:%d'%(authhost,authport))
    yex.set_value(YAML_ACCEPT_TERMS_OF_USE_KEYWORD,True)
    yex.set_value(YAML_SUGGESTED_FEE_RECIPIENT_KEYWORD,make_address_checksum('0x%s'%(keyaddress)))
    yex.set_value(YAML_MINIMUM_PEERS_PER_SUBNET_KEYWORD,0)
    yex.set_value(YAML_P2P_TCP_PORT_KEYWORD,curport)
    yex.set_value(YAML_P2P_UDP_PORT_KEYWORD,curport)
    curport += 1
    yex.set_value(YAML_MONITOR_PORT_KEYWORD,curport)
    curport += 1
    yex.set_value(YAML_VERBOSITY_KEYWORD,'trace')
    yex.set_value(YAML_LOG_FORMAT_KEYWORD,'simple')
    yex.set_value(YAML_LOG_FILES_KEYWORD,[logfile])
    yex.set_value(YAML_SLASHER_KEYWORD,False)
    outs = yex.dumps()
    write_file(outs,yamlfile)
    return curport

def make_validator_config_file(args,username,startport,startidx):
    beaconcfg = datadir_file(args,username,'beacon_config.yaml')
    validaotrcfg = datadir_file(args,username,'validator_config.yaml')
    validatordir = datadir_file(args,username,'validatordir')
    chaincfgfile = datadir_file(args,username,'genesis_config.yaml')
    logfile = datadir_file(args,username,'validator_%s.log'%(username))
    byex = YamlEx()
    ins = read_file(beaconcfg)
    byex.loads(ins)
    vyex = YamlEx()
    rpcport = byex.get_value(YAML_RPC_PORT_KEYWORD)
    rpchost = byex.get_value(YAML_RPC_HOST_KEYWORD)
    if rpcport is None or rpchost is None:
        raise Exception('%s not set [%s] or [%s]'%(beaconcfg,YAML_RPC_HOST_KEYWORD,YAML_RPC_PORT_KEYWORD))
    vyex.set_value(YAML_VALIDATOR_BEACON_RPC_PROVIDER_KEYWORD,'%s:%s'%(rpchost,rpcport))
    vyex.set_value(YAML_DATADIR_KEYWORD,validatordir)
    vyex.set_value(YAML_ACCEPT_TERMS_OF_USE_KEYWORD,True)
    vyex.set_value(YAML_INTEROP_NUM_VALIDATORS_KEYWORD,1)
    curport = startport
    vyex.set_value(YAML_INTEROP_START_IDX_KEYWORD,startidx)
    vyex.set_value(YAML_RPC_PORT_KEYWORD,curport)
    curport += 1
    vyex.set_value(YAML_GRPC_GATEWAY_PORT_KEYWORD,curport)
    curport += 1
    vyex.set_value(YAML_MONITOR_PORT_KEYWORD,curport)
    curport += 1
    vyex.set_value(YAML_GRAFFITI_KEYWORD,'node-%d'%(startidx))
    if not os.path.exists(chaincfgfile):
        shutil.copyfile(args.chainconfigfile,chaincfgfile)
    vyex.set_value(YAML_CHAIN_CONFIG_FILE_KEYWORD,chaincfgfile)
    vyex.set_value(YAML_LOG_FILES_KEYWORD,[logfile])
    vyex.set_value(YAML_LOG_FORMAT_KEYWORD,'simple')
    vyex.set_value(YAML_VERBOSITY_KEYWORD,'trace')
    vyex.set_value(YAML_DISABLE_EPHEMERAL_LOG_FILE_KEYWORD,True)
    outs = vyex.dumps()
    write_file(outs,validaotrcfg)
    return curport






def start_beacon(args,username):
    beaconcfg = datadir_file(args,username,'beacon_config.yaml')
    cmds = []
    cmds.append(get_prysm_bin(args,'beacon-chain'))
    cmds.append('--config-file')
    cmds.append(beaconcfg)
    devnullfile = open(os.devnull,'wb')
    if is_windows():
        flags = 0
        flags |= 0x00000008  # DETACHED_PROCESS
        flags |= 0x00000200  # CREATE_NEW_PROCESS_GROUP
        flags |= 0x08000000  # CREATE_NO_WINDOW

        pkwargs = {
            'close_fds': True,  # close stdin/stdout/stderr on child
            'creationflags': flags,
        }
        p = subprocess.Popen(cmds,stdout=devnullfile,stderr=devnullfile)
    else:
        logging.info('cmds %s'%(cmds))
        p = subprocess.Popen(cmds,stdout=devnullfile,stderr=devnullfile)
    return p

def start_validator(args,username):
    validatorcfg = datadir_file(args,username,'validator_config.yaml')
    cmds = []
    cmds.append(get_prysm_bin(args,'validator'))
    cmds.append('--config-file')
    cmds.append(validatorcfg)
    devnullfile = open(os.devnull,'wb')
    if is_windows():
        flags = 0
        flags |= 0x00000008  # DETACHED_PROCESS
        flags |= 0x00000200  # CREATE_NEW_PROCESS_GROUP
        flags |= 0x08000000  # CREATE_NO_WINDOW

        pkwargs = {
            'close_fds': True,  # close stdin/stdout/stderr on child
            'creationflags': flags,
        }
        logging.info('cmds %s'%(cmds))
        p = subprocess.Popen(cmds,stdout=devnullfile,stderr=devnullfile)
    else:
        logging.info('cmds %s'%(cmds))
        p = subprocess.Popen(cmds,stdout=devnullfile,stderr=devnullfile)
    return p


def startbeacon_handler(args,parser):
    set_logging(args)
    ins = read_file(args.subnargs[0])
    rdict = json.loads(ins)
    keys = []
    for k in rdict.keys():
        keys.append(k)
    # now to make sure every key
    startport = 8200
    for k in keys:
        make_beacon_config_file(args,k,rdict,startport)
        startport += 20
    for k in keys:
        p = start_beacon(args,k)
        if args.verbose == 0:
            sys.stdout.write('beacon-chain [%d]\n'%(p.pid))
    sys.exit(0)

def startvalidator_handler(args,parser):
    set_logging(args)
    verbose_zero = False
    if args.verbose == 0:
        verbose_zero = True
    ins = read_file(args.subnargs[0])
    rdict = json.loads(ins)
    keys = []
    for k in rdict.keys():
        keys.append(k)
    # now to make sure every key
    startport = 9200
    idx = 0
    for k in keys:
        make_validator_config_file(args,k,startport,idx)
        startport += 20
        idx += 1

    for k in keys:
        p = start_validator(args,k)
        if verbose_zero:
            sys.stdout.write('validator [%d]\n'%(p.pid))
    sys.exit(0)
    return

def kill_proc_inner(args,progname):
    verbose_zero = False
    if args.verbose == 0:
        verbose_zero = True

    if verbose_zero:
        sys.stdout.write('current %s\n'%(os.getpid()))
    ps = ProcExpolore()
    errcnt = 0
    while True:
        pids = []
        errcnt += 1
        retval = ps.snapshot()
        if not retval:
            continue
        res = ps.get_result()
        for k,v in res.items():
            if is_windows():
                if v.firstarg == '%s.exe'%(progname) or v.firstarg.endswith('\\%s.exe'%(progname)):
                    if verbose_zero:
                        try:
                            sys.stdout.write('add [%s]\n'%(k))
                        except:
                            pass
                    pids.append(k)
            else:
                if v.firstarg == '%s'%(progname) or v.firstarg.endswith('/%s'%(progname)):
                    if verbose_zero:
                        try:
                            sys.stdout.write('add [%s]\n'%(k))
                        except:
                            pass
                    pids.append(k)
        if len(pids) == 0:
            if verbose_zero:
                try:
                    sys.stdout.write('pids []\n')
                except:
                    pass
            break
        idx = 0
        while idx < len(pids):
            p = pids[idx]
            if verbose_zero:
                try:
                    sys.stdout.write('[%s]\n'%(p))
                except:
                    logging.error('%s'%(traceback.format_exc()))
            try:
                if is_windows():
                    os.kill(p,signal.CTRL_C_EVENT)
                else:
                    os.kill(p,signal.SIGINT)
            except:
                logging.error('%s'%(traceback.format_exc()))
            idx += 1
    return

def list_proc_inner(args,progname):
    ps = ProcExpolore()
    errcnt = 0
    retdict = dict()
    while True:
        pids = []
        errcnt += 1
        retval = ps.snapshot()
        if not retval:
            continue
        res = ps.get_result()
        for k,v in res.items():
            if is_windows():
                if v.firstarg == '%s.exe'%(progname) or v.firstarg.endswith('\\%s.exe'%(progname)):
                    retdict[k] = v
            else:
                if v.firstarg == '%s'%(progname) or v.firstarg.endswith('/%s'%(progname)):
                    retdict[k] = v
        return retdict
    return retdict


def stopbeacon_handler(args,parser):
    set_logging(args)
    kill_proc_inner(args,'beacon-chain')
    sys.exit(0)

def stopvalidator_handler(args,parser):
    set_logging(args)
    kill_proc_inner(args,'validator')
    sys.exit(0)

def listproc_handler(args,parser):
    set_logging(args)
    procs = ['validator','beacon-chain']
    if len(args.subnargs) > 0:
        procs = args.subnargs
    for p in procs:
        rdict = list_proc_inner(args,p)
        for k,v in rdict.items():
            sys.stdout.write('[%s] %s [%s]\n'%(p,k,v.cmdline))
    sys.exit(0)
    return

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
        },
        "startbeacon<%s.startbeacon_handler>##listjson to start beacon for list##" : {
            "$" : 1
        },
        "stopbeacon<%s.stopbeacon_handler>##to stop beacon running##" : {
            "$" : 0
        },
        "startvalidator<%s.startvalidator_handler>##listjson to start validator##" : {
            "$" : 1
        },
        "stopvalidator<%s.stopvalidator_handler>##to stop beacon running##" : {
            "$" : 0
        },
        "listproc<%s.listproc_handler>##to list proc##" : {
            "$" : "*"
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

    commandline = commandline_fmt%(repltopdir,repldatadir,replgethdir,replgethdatadir,replchainconfigfile,forks,deffork,__name__,support_bin_dir,__name__,__name__,__name__,__name__,__name__,__name__,__name__,__name__)
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