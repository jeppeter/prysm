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
        "force|F" : false,
        "compile<%s.compile_handler>##bins ... to compile bins now support is %s ##" : {
            "$" : "+"
        },
        "checkenv<%s.checkenv_handler>##to check environment to compile##" : {
            "$" : 0
        }


    }
    '''
    topdir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
    support_binnames = get_support_bin(topdir)
    support_bin_dir = ''
    for d in support_binnames:
        if len(support_bin_dir) > 0:
            support_bin_dir += ','
        support_bin_dir += '%s'%(d)
    repltopdir = topdir
    if is_windows():
        repltopdir = repltopdir.replace('\\','\\\\')

    commandline = commandline_fmt%(repltopdir,__name__,support_bin_dir,__name__)
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