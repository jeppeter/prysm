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
import rlp
import struct
from Crypto.Hash import keccak


sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__))))

from loglib import set_logging, load_log_commandline,log_command_prefix
from fileop import read_file,write_file,make_directory_safe,mktemp_file,read_file_bytes,write_file_bytes
from envop import is_windows,is_linux
from tomlex import TomlEx
from strop import rand_buffer,dump_buffer,parse_int


class LmdAttest(object):
    def __init__(self):
        self.key = ''
        self.weight = 0
        self.validatorid = -1
        return
    def set_attest(self,key,weight,validatorid):
        self.key = key
        self.weight = weight
        self.validatorid = validatorid
        return

class LmdAttestMap(object):
    def __init__(self):
        self.rdict = dict()
        return

    def set_node(self,validatorid,attest):
        self.rdict[validatorid]= attest
        return


class LmdDagNode(object):
    def __init__(self):
        self.idx = -1
        self.key = ''
        self.weight = -1
        self.parent = None
        self.besttarget = -1
        self.ishead = False
        self.slot = -1
        return
    def set_node(self,idx,key,weight,besttarget,slot,ishead = False,parent=None):
        self.idx = idx
        self.key = key
        self.weight = weight
        self.parent = parent
        self.besttarget = target
        self.ishead = ishead
        self.slot = slot
        return

class LmdDagTree(object):
    def __init__(self):
        self.rdict = dict()
        return

    def set_node(self,key,dag):
        self.rdict[key]= dag
        return

class LmdPair(object):
    def __init__(self):
        self.dagtree = None
        self.atttree = None
        return

    def set_pair(self,dag, att):
        self.dagtree = dag
        self.atttree = att
        return

    def check_pair(self):
        # to calculate the handle
        maxval = dict()
        for k,v in self.atttree:
            if k not in maxval.keys():
                maxval[k] = 0
            maxval[k] += v.weight
        selval = 0
        selkey = None
        for k ,v in maxval:
            if v > selval:
                selkey = k

        # now to check for the select
        




class LmdFilter(object):
    def __init__(self,fname):
        self.fname= fname
        self.pairs = []
        return

    def _calc_tabs(self,tabstr):
        idx = 0
        curtabs = ''
        while True:
            if curtabs == tabstr:
                break
            if len(curtabs) > len(tabstr):
                raise Exception('not valid tabstr [%s][%d]'%(tabstr,len(tabstr)))
            curtabs += '    '
            idx += 1
        return idx
    def parse(self):
        ins = read_file(self.fname)
        sarr = re.split('\n',ins)
        nextattexpr = re.compile('.*\\s+agor$')
        nextdagexpr = re.compile('.*\\s+HeadFn$')
        isatt = False
        isdag = False
        dagexpr = re.compile('^(\\s*)(\\*)?\\[([0-9]+)\\]DagNode\\[Key\\s+([0-9a-fA-F]+)\\s+Slot\\s+([0-9a-fA-FxX]+)\\s+Height\\s+([0-9a-fA-FxX]+)\\s+Weight\\s+([0-9a-fA-FxX]+)\\s+Proposer\\s+([0-9a-fA-FxX]+)(\\s+Parent\\.Key\\s+([0-9a-f]+))?\\]\\s+bestchild\\s+([^ ]+)\\s+weight\\s+([0-9]+)\\s+besttarget\\s([0-9]+)$')
        attexpr = re.compile('^\\[([0-9]+)\\]\\s+Attestation\\[BeaconBlockRoot\\s+([a-f0-9A-F]+)\\s+ValidatorID\\s+([0-9a-fx]+)\\s+Weight\\s+([0-9a-fx]+)\\]$')
        curdagtree = None
        curatttree = None
        curpair = None
        dagpushs = []

        for l in sarr:
            l = l.rstrip('\n\r')
            if not isatt and not isdag:
                if nextattexpr.match(l):
                    isatt = True
                    curatttree = LmdAttestMap()
                    continue
                if nextdagexpr.match(l):
                    isdag = True
                    curdagtree = LmdDagTree()
                    dagpushs = []                    
                    continue
            if isatt:
                m = attexpr.findall(l)
                if m is None or len(m) == 0 or len(m[0]) < 4:
                    isatt = False
                    continue
                curatt = LmdAttest()
                validatorid = parse_int(m[0][2])
                key = m[0][1]
                weight = parse_int(m[0][3])
                curatt.set_attest(key,weight,validatorid)
                curatttree.set_node(curatt.validatorid,curatt)
                continue
            if isdag:
                m = dagexpr.findall(l)
                if m is None or len(m) == 0 or len(m[0]) < 13:
                    lmdpair = LmdPair()
                    lmdpair.set_pair(curatttree,curdagtree)
                    self.pairs.append(lmdpair)
                    curatttree = None
                    curdagtree = None
                    dagpushs = []
                    continue
                tabs = self._calc_tabs(m[0][0])
                ishead = False
                if m[0][1] == '*':
                    ishead = True
                idx = parse_int(m[0][2])
                key = m[0][3]
                slot = parse_int(m[0][4])
                height = parse_int(m[0][11])
                if m[0][10] == 'nonExistentNode':
                    bestchild = -1
                else:
                    bestchild = parse_int(m[0][10])
                besttarget = parse_int(m[0][12])
                # now to check the best                
                parent = None
                if tabs > 0:
                    if tabs >= len(dagpushs):
                        parent = dagpushs[-1]
                        dagpushs.append(key)
                    else:
                        curidx = len(dagpushs)
                        while len(dagpushs) > tabs:
                            dagpushs = dagpushs[:-2]
                        parent = dagpushs[-1]
                        dagpushs.append(key)
                curdag = LmdDagNode()
                curdag.set_node(idx,key,weight,besttarget,slot,ishead,parent)
                curdagtree.set_node(key,curdag)
                continue




def lmdfilter_handler(args,parser):
    set_logging(args)
    ins = read_file(args.input)
    sarr = re.split('\n',ins)


    sys.exit(0)

def load_base_parser(parser):
    commandline_fmt='''
    {
        "input|i" : null,
        "output|o" : null,
        "lmdfilter<%s.lmdfilter_handler>##to filter lmd struct from input as output for %s##" : {
            "$" : 0
        }
    }
    '''
    lmdfile = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','testing','lmd-ghost','lmd-ghost'))
    commandline = commandline_fmt%(__name__,lmdfile)
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