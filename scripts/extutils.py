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


class CmpObject(object):
    def __init__(self):
        return

    def cmp_dict_raise(self,sdict,odict,note,raiseexp):
        for k in sdict.keys():
            if k not in odict.keys():
                if raiseexp:
                    raise Exception('%s self [%s] not in other'%(note,k))
                return False
            if sdict[k] != odict[k]:
                if raiseexp:
                    raise Exception('%s self [%s] [%s] != other [%s] [%s]'%(note,k,sdict[k],k,odict[k]))
                return False

        for k in odict.keys():
            if k not in sdict.keys():
                if raiseexp:
                    raise Exception('%s other [%s] not in self'%(note,k))
                return False
            if sdict[k] != odict[k]:
                if raiseexp:
                    raise Exception('%s other [%s] [%s] != self [%s] [%s]'%(note,k,odict[k],k,sdict[k]))
                return False
        return True

    def cmp_list_raise(self,sarr,oarr,note,raiseexp):
        if sarr != oarr:
            if raiseexp:
                if len(sarr) != len(oarr):
                    raise Exception('%s len (%d) != len (%d)'%(note,len(sarr),len(oarr)))
                idx = 0
                while idx < len(sarr):
                    if sarr[idx] != oarr[idx]:
                        raise Exception('%s [%d] [%d] != [%d]'%(note,idx,sarr[idx],oarr[idx]))
                    idx += 1
            return False
        return True

    def cmp_value_raise(self,sval,oval,note,raiseexp):
        if sval != oval:
            if raiseexp:
                raise Exception('%s sval %s != oval %s'%(note,sval,oval))
            return False
        return True



class LmdAttest(object):
    def __init__(self):
        self.key = ''
        self.weight = 0
        self.validatorid = -1
        self.lindex = -1
        return
    def set_attest(self,key,weight,validatorid):
        self.key = key
        self.weight = weight
        self.validatorid = validatorid
        return

    def set_lindex(self,lindex):
        self.lindex = lindex
        return

    def string(self):
        rets = 'Attest(Key %s weight 0x%x validatorid %d lindex %d)'%(self.key,self.weight,self.validatorid,self.lindex)
        return rets

    def __str__(self):
        return self.string()

    def __repr__(self):
        return self.string()

class LmdAttestMap(object):
    def __init__(self,lindex):
        self.rdict = dict()
        self.lindex = lindex
        return

    def set_node(self,validatorid,attest):
        self.rdict['%s'%(validatorid)]= attest
        return


class ScoreChange(object):
    def __init__(self):
        self.key = ''
        self.score = 0
        self.validatorid = -1
        self.slot = slot
        return

    def set_key(self,key):
        self.key = key
        return

    def set_score(self,score):
        self.score = score
        return

    def set_validatorid(self,validatorid):
        self.validatorid = validatorid
        return

    def set_slot(self,slot):
        self.slot = slot
        return



class ScoreChange(object):
    def __init__(self):
        self.att = None
        self.scorechange = 0
        self.lindex = -1
        return

    def set_score(self,score):
        self.scorechange = score
        return

    def set_lindex(self,lindex):
        self.lindex = lindex
        if self.att is not None:
            self.att.set_lindex(lindex)
        return

    def set_att(self,key,weight,validatorid):
        if self.att is None:
            self.att = LmdAttest()
            if self.lindex > 0:
                self.att.set_lindex(lindex)
        self.att.set_attest(key,weight,validatorid)
        return

class DagNode(object):
    def __init__(self):
        self.idx = -1
        self.key = ''
        self.weight = -1
        self.parent = None
        self.slot = -1
        self.lindex = -1
        self.validatorid = -1
        return

    def set_lindex(self,lindex):
        self.lindex = lindex
        return
    def set_key(self,key):
        self.key = key
        return

    def set_weight(self,weight):
        self.weight = weight
        return

    def set_slot(self,slot):
        self.slot = slot
        return

    def set_parent(self,parent):
        self.parent = parent
        return

    def set_validatorid(self,validatorid):
        self.validatorid = validatorid
        return



class LmdDagNode(CmpObject):
    def __init__(self):
        self.lindex = -1
        self.idx = -1
        self.key = ''
        self.weight = -1
        self.parent = None
        self.besttarget = -1
        self.ishead = False
        self.slot = -1
        self.bestchild = -1
        return

    def deep_copy(self):
        ret = LmdDagNode()
        ret.set_lindex(self.lindex)
        ret.set_idx(self.idx)
        ret.set_key(self.key)
        ret.set_weight(self.weight)
        ret.set_parent(self.parent)
        ret.set_besttarget(self.besttarget)
        ret.set_ishead(self.ishead)
        ret.set_slot(self.slot)
        ret.set_bestchild(self.bestchild)
        return ret


    def eq_op(self,other,raiseexp=False):
        retval = self.cmp_value_raise(self.idx,other.idx,'idx',raiseexp)
        if not retval:
            return False
        retval = self.cmp_value_raise(self.key,other.key,'key',raiseexp)
        if not retval:
            return False
        retval = self.cmp_value_raise(self.weight,other.weight,'weight',raiseexp)
        if not retval:
            return False
        retval = self.cmp_value_raise(self.parent,other.parent,'parent',raiseexp)
        if not retval:
            return False
        retval = self.cmp_value_raise(self.ishead,other.ishead,'ishead',raiseexp)
        if not retval:
            return False
        retval = self.cmp_value_raise(self.slot,other.slot,'slot',raiseexp)
        if not retval:
            return False
        retval = self.cmp_value_raise(self.bestchild,other.bestchild,'bestchild',raiseexp)
        if not retval:
            return False
        return True


    def __eq__(self,other):
        return self.eq_op(other,False)

    def __ne__(self,other):
        return not self.eq_op(other,False)

    def set_lindex(self,lindex):
        self.lindex = lindex
        return
    def set_key(self,key):
        self.key = key
        return

    def set_idx(self,idx):
        self.idx = idx
        return

    def set_weight(self,weight):
        self.weight = weight
        return

    def set_bestchild(self,bestchild):
        self.bestchild = bestchild
        return

    def set_besttarget(self,besttarget):
        self.besttarget = besttarget
        return

    def set_slot(self,slot):
        self.slot = slot
        return

    def set_ishead(self,ishead):
        self.ishead = ishead
        return

    def set_idx(self,idx):
        self.idx = idx
        return

    def set_parent(self,parent):
        self.parent = parent
        return

    def set_node(self,lindex,idx,key,weight,besttarget,bestchild,slot,ishead = False,parent=None):
        self.idx = idx
        self.key = key
        self.weight = weight
        self.parent = parent
        self.besttarget = besttarget
        self.ishead = ishead
        self.slot = slot
        self.lindex = lindex
        self.bestchild = bestchild
        return

class LmdDagTree(CmpObject):
    def __init__(self,lindex):
        self.rdict = dict()
        self.childmap = dict()
        self.idxdict = dict()
        self.ridxdict = dict()
        self.lindex = lindex
        self.root = None
        return

    def set_node(self,key,dag):
        self.rdict[key]= dag
        return
    def set_index_node(self,idx,key):
        if self.root is None:
            self.root = key
        self.idxdict['%d'%(idx)] = key
        self.ridxdict[key] = idx
        return

    def set_child(self,parent,key):
        if parent is None:
            return
        if parent not in self.childmap.keys():
            self.childmap[parent] = []
        self.childmap[parent].append(key)
        return

    def _find_head_key(self,parentkey):
        if parentkey in self.rdict.keys():
            v = self.rdict[parentkey]
            if v.ishead:
                return v
        if parentkey in self.childmap.keys():
            chlds = self.childmap[parentkey]
            idx = 0
            while idx < len(chlds):
                retval = self._find_head_key(chlds[idx])
                if retval is not None:
                    return retval
                idx += 1
        return None

    def cmp_child_map(self,scmap,ocmap,note,raiseexp):
        for k in scmap.keys():
            if k not in ocmap.keys():
                if raiseexp:
                    raise Exception('%s key [%s] not in ocmap'%(note,k))
                return False
            sarr = scmap[k]
            oarr = ocmap[k]
            if len(sarr) != len(oarr):
                if raiseexp:
                    raise Exception('%s key [%s] scmap len(%d) != ocmap len(%d)'%(note,k,len(sarr),len(oarr)))
                return False
            idx = 0
            while idx < len(sarr):
                if sarr[idx] not in oarr:
                    if raiseexp:
                        raise Exception('%s key [%s] sarr[%d] val [%s] not in ocmap %s'%(note,k,idx,sarr[idx],oarr))
                    return False
                idx += 1
        for k in ocmap.keys():
            if k not in scmap.keys():
                if raiseexp:
                    raise Exception('%s key [%s] not in scmap'%(note,k))
                return False
            sarr = scmap[k]
            oarr = ocmap[k]
            if len(sarr) != len(oarr):
                if raiseexp:
                    raise Exception('%s key [%s] scmap len(%d) != ocmap len(%d)'%(note,k,len(sarr),len(oarr)))
                return False
            idx = 0
            while idx < len(oarr):
                if oarr[idx] not in sarr:
                    if raiseexp:
                        raise Exception('%s key [%s] oarr[%d] val [%s] not in scmap %s'%(note,k,idx,oarr[idx],sarr))
                    return False
                idx += 1
        return True



    def eq_op(self,other,raiseexp=False):
        retval = self.cmp_dict_raise(self.rdict,other.rdict,'rdict',raiseexp)
        if not retval:
            return False
        retval = self.cmp_child_map(self.childmap,other.childmap,'childmap',raiseexp)
        if not retval:
            return False
        retval = self.cmp_dict_raise(self.idxdict,other.idxdict,'idxdict',raiseexp)
        if not retval:
            return False
        retval = self.cmp_dict_raise(self.ridxdict,other.ridxdict,'ridxdict',raiseexp)
        if not retval:
            return False
        retval = self.cmp_value_raise(self.root,other.root,'root',raiseexp)
        if not retval:
            return False
        return True

    def __eq__(self,other):
        return self.eq_op(other,False)

    def __ne__(self,other):
        return not self.eq_op(other,False)


    def get_head_node(self,parentkey):
        return self._find_head_key(parentkey)

    def check_best_child_as_head(self,headidx):
        retval = False
        if self.root is None:
            return retval
        if self.root not in self.rdict.keys():
            return retval
        curdag = self.rdict[self.root]
        while True:
            if headidx == curdag.idx:
                if curdag.key not in self.childmap.keys():
                    return True
                else:
                    chlds = self.childmap[curdag.key]
                    if len(chlds) > 0:
                        logging.error('line[%d] %s hash children'%(self.lindex,curdag.key))
                        return False
                    return True
            if curdag.key not in self.childmap.keys():
                # no childs so can not handle
                logging.error('line[%d] %s no key in childmap'%(self.lindex,curdag.key))
                return False

            chlds = self.childmap[curdag.key]
            if curdag.bestchild < 0:
                logging.error('line[%d] %s bestchild %d < 0'%(self.lindex,curdag.key,curdag.bestchild))
                return False
            if '%d'%(curdag.bestchild) not in self.idxdict.keys():
                logging.error('line[%d] %s bestchild %d not find in idxdict'%(self.lindex,curdag.key,curdag.bestchild))
                return False
            chldkey = self.idxdict['%d'%(curdag.bestchild)]

            if chldkey not in chlds:
                logging.error('line[%d] %s bestchild %d not in chlds %s'%(self.lindex,curdag.key,curdag.bestchild,chlds))
                return False
            if chldkey not in self.rdict.keys():
                logging.error('line[%d] %s not find for bestchild %d as %s'%(self.lindex,chldkey,curdag.bestchild,curdag.key))
                return False
            curdag = self.rdict[chldkey]


class ProtoArrayLMDGhost(CmpObject):
    def __init__(self):
        self.lindex = -1
        self.weights = []
        self.bestchilds = []
        self.indices = dict()
        self.nodes = []
        self.parents = []
        self.targets = []
        return

    def deep_copy(self):
        retgh = ProtoArrayLMDGhost()
        retgh.set_lindex(self.lindex)
        retgh.set_weights(self.weights)
        retgh.set_bestchilds(self.bestchilds)
        retgh.set_indices(self.indices)
        retgh.set_nodes(self.nodes)
        retgh.set_parents(self.parents)
        retgh.set_targets(self.targets)
        return retgh

        


    def eq_op(self,other,raiseexp=False):
        retval = self.cmp_list_raise(self.weights,other.weights,'weights',raiseexp)
        if not retval:
            return False
        retval = self.cmp_list_raise(self.bestchilds,other.bestchilds,'bestchilds',raiseexp)
        if not retval:
            return False
        retval = self.cmp_dict_raise(self.indices,other.indices,'indices',raiseexp)
        if not retval:
            return False
        retval = self.cmp_list_raise(self.nodes,other.nodes,'nodes',raiseexp)
        if not retval:
            return False
        retval = self.cmp_list_raise(self.targets,other.targets,'targets',raiseexp)
        if not retval:
            return False
        retval = self.cmp_list_raise(self.parents,other.parents,'parents',raiseexp)
        if not retval:
            return False
        return True

    def __eq__(self,other):
        return self.eq_op(other,False)

    def __ne__(self,other):
        return not self.eq_op(other,False)

    def set_lindex(self,lindex):
        self.lindex = lindex
        return

    def set_weights(self,s):
        try:
            if isinstance(s, str):
                nv = json.loads(s)
            elif isinstance(s,list):
                nv = s
            else:
                raise Exception('can not set weights %s'%(s))
            self.weights = nv
        except:
            logging.error('%s'%(traceback.format_exc()))
        return

    def set_bestchilds(self,s):
        try:
            if isinstance(s, str):
                nv = json.loads(s)
            elif isinstance(s,list):
                nv = s
            else:
                raise Exception('can not set bestchilds %s'%(s))
            self.bestchilds = nv
        except:
            logging.error('%s'%(traceback.format_exc()))
        return

    def set_indices(self,s):
        try:
            if isinstance(s, str):
                nv = json.loads(s)
            elif isinstance(s,dict):
                nv = s
            else:
                raise Exception('can not set indices %s'%(s))
            self.indices = nv
            self.nodes = [''] * len(self.indices.keys())
            for (k,v) in self.indices.items():
                self.nodes[v] = k
        except:
            logging.error('%s'%(traceback.format_exc()))
        return

    def set_parents(self,s):
        try:
            if isinstance(s, str):
                nv = json.loads(s)
            elif isinstance(s,list):
                nv = s
            else:
                raise Exception('can not set parents %s'%(s))
            self.parents = nv
        except:
            logging.error('%s'%(traceback.format_exc()))
        return

    def set_targets(self,s):
        try:
            if isinstance(s, str):
                nv = json.loads(s)
            elif isinstance(s,list):
                nv = s
            else:
                raise Exception('can not set targets %s'%(s))
            self.targets = nv
        except:
            logging.error('%s'%(traceback.format_exc()))
        return

PROTO_NOTE_EXPR_STR = '^.*ProtoArrayLMDGhost\\.note\\s+(.*)$'
PROTO_BESTCHILDS_EXPR_STR = '^.*ProtoArrayLMDGhost\\.bestchild\\s+(\\[[0-9\\-,]+\\])$'
PROTO_WEIGHT_EXPR_STR = '^.*ProtoArrayLMDGhost\\.weight\\s+(\\[[0-9,]+\\])$'
PROTO_PARENT_EXPR_STR = '^.*ProtoArrayLMDGhost\\.parent\\s+(\\[[0-9\\-,]+\\])$'
PROTO_TARGET_EXPR_STR = '^.*ProtoArrayLMDGhost\\.target\\s+(\\[[0-9,]+\\])$'
PROTO_INDICES_EXPR_STR = '^.*ProtoArrayLMDGhost\\.indices\\s+(.*)$'
PROTO_NODE_EXPR_STR = '^.*ProtoArrayLMDGhost\\.node\\s+(.*)$'
NEWNODE_DAG_EXPR_STR = '^.*OnNewNode\\.DagNode\\s+DagNode\\[Key\\s+([a-f0-9]+)\\s+Slot\\s+([0-9xa-f]+)\\s+Height\\s+([0-9xa-f]+)\\s+Weight\\s+([0-9xa-f]+)\\s+Proposer\\s+([0-9xa-f]+)(\\s+Parent\\.Key\\s+([0-9a-f]+))?\\]$'
APPLYCHANGE_SCORECHANGE_EXPR_STR = '^.*ApplyScoreChanges\\.ScoreChange\\s+ScoreChange\\[\\s+Target\\s+DagNode\\[Key\\s+([a-f0-9]+)\\s+Slot\\s+([0-9xa-f]+)\\s+Height\\s+([0-9xa-f]+)\\s+Weight\\s+([0-9xa-f]+)\\s+Proposer\\s+([0-9xa-f]+)(\\s+Parent\\.Key\\s+([0-9a-f]+))?\\]\\s+ScoreDelta\\s+([0-9a-f\\-x]+)\\]$'

class ParseProtoArray(object):
    def __init__(self):
        self.protoarray = None
        return


    def parse(self,lindex,sarr):
        passed = lindex
        self.protoarray = None
        bestchildexpr = re.compile(PROTO_BESTCHILDS_EXPR_STR)
        weightexpr = re.compile(PROTO_WEIGHT_EXPR_STR)
        parentexpr = re.compile(PROTO_PARENT_EXPR_STR)
        targetexpr = re.compile(PROTO_TARGET_EXPR_STR)
        indicesexpr = re.compile(PROTO_INDICES_EXPR_STR)
        nodeexpr = re.compile(PROTO_NODE_EXPR_STR)
        while passed < len(sarr):
            l = sarr[passed]
            l = l.rstrip('\r\n')
            m = bestchildexpr.findall(l)
            if m is not None and len(m) > 0:
                if self.protoarray is None:
                    self.protoarray = ProtoArrayLMDGhost()
                    self.protoarray.set_lindex(lindex)
                self.protoarray.set_bestchilds(m[0])
                passed += 1
                continue
            m = weightexpr.findall(l)
            if m is not None and len(m) > 0:
                if self.protoarray is None:
                    self.protoarray = ProtoArrayLMDGhost()
                    self.protoarray.set_lindex(lindex)
                self.protoarray.set_weights(m[0])
                passed += 1
                continue
            m = parentexpr.findall(l)
            if m is not None and len(m) > 0:
                if self.protoarray is None:
                    self.protoarray = ProtoArrayLMDGhost()
                    self.protoarray.set_lindex(lindex)
                self.protoarray.set_parents(m[0])
                passed += 1
                continue



            
        return passed

class LmdPair(object):
    def __init__(self):
        self.dagtree = None
        self.atttree = None
        return

    def set_pair(self,dag, att):
        self.dagtree = dag
        self.atttree = att
        self.errors = []
        return

    def _check_attest_key(self,selkey,nwdict,headidx):
        if selkey not in self.dagtree.rdict.keys():
            self.errors.append('[%d] selkey %s not found in dagtree'%(self.dagtree.lindex,selkey))
            return False
        curdag = self.dagtree.rdict[selkey]        
        if curdag.key not in self.dagtree.childmap.keys():
            if curdag.idx == headidx:
                return True
            for (k,v) in nwdict.items():
                self.errors.append('[%d] [%s] = [%d]'%(self.dagtree.lindex,k,v))
            self.errors.append('[%d] key %s no childs'%(self.dagtree.lindex,curdag.key))
            return False
        chlds = self.dagtree.childmap[curdag.key]
        # now to make sure the values
        selkeys = []
        selval = 0
        for key in chlds:
            if key in nwdict.keys():
                if nwdict[key] > selval:
                    selval = nwdict[key]
                    selkeys = [key]
                elif nwdict[key] == selval:
                    selkeys.append(key)
                    
        if len(selkeys) == 0:
            # this will pickup the 
            fdag = self.dagtree.get_head_node(curdag.key)
            if fdag is None:
                for (k,v) in nwdict.items():
                    self.errors.append('[%d] [%s] = [%d]'%(self.dagtree.lindex,k,v))
                self.errors.append('[%d] key %s children not found in nwdict'%(self.dagtree.lindex,curdag.key))
                logging.info(' ')
                return False
            if fdag.idx != headidx:
                for (k,v) in nwdict.items():
                    self.errors.append('[%d] [%s] = [%d]'%(self.dagtree.lindex,k,v))
                self.errors.append('[%d] key %s children not match idx'%(self.dagtree.lindex,curdag.key))
                logging.info(' ')
                return False
            return True
        for ckey in selkeys:
            retval = self._check_attest_key(ckey,nwdict,headidx)
            if retval:
                return True
        return False

    def _format_tab(self,tabs):
        outs = ''
        idx = 0
        while idx < tabs:
            outs += '    '
            idx += 1
        return outs

    def _output_nwdict(self,key,nwdict,tabs):
        outs = ''
        if key not in nwdict.keys():
            return outs
        outs += self._format_tab(tabs)
        outs += '%s weight %d\n'%(key,nwdict[key])
        if key in self.dagtree.childmap.keys():
            chlds = self.dagtree.childmap[key]
            for k in chlds:
                if k in nwdict.keys():
                    outs += self._output_nwdict(k,nwdict,tabs+1)
        return outs



    def check_attest(self,headidx):
        # now to give the weights
        wdict = dict()
        hkeys = []
        for (k,v) in self.atttree.rdict.items():
            if v.key not in wdict.keys():
                wdict[v.key] = 0
            wdict[v.key] += v.weight
        nwdict = dict()
        for (k,weight) in wdict.items():
            if k not in nwdict.keys():
                nwdict[k] = 0
            #logging.info('nwdict[%s] += %d (%d => %d)'%(k,weight,nwdict[k],nwdict[k] + weight))
            nwdict[k] += weight
            if k in self.dagtree.rdict.keys():
                curdag = self.dagtree.rdict[k]
                # now we add the value for the parent
                curparent = curdag.parent
                while curparent is not None:
                    if curparent not in self.dagtree.rdict.keys():
                        sys.stderr.write('[%d] not find parent %s\n'%(self.dagtree.lindex,curparent))
                        return False
                    if curparent not in nwdict.keys():
                        nwdict[curparent] = 0
                    #logging.info('nwdict[%s] += %d (%d => %d)'%(curparent,weight,nwdict[curparent],nwdict[curparent] + weight))
                    nwdict[curparent] += weight
                    curdag = self.dagtree.rdict[curparent]
                    curparent = curdag.parent
        # now we should check for the values
        logging.info('\n%s'%(self._output_nwdict(self.dagtree.root,nwdict,0)))
        if self.dagtree.root is None:
            sys.stderr.write('[%d] no root\n'%(self.dagtree.lindex))
            return False
        self.errors = []
        retval = self._check_attest_key(self.dagtree.root,nwdict,headidx)
        if not retval:
            for l in self.errors:
                sys.stderr.write('%s\n'%(l))
            return False
        return True



    def check_pair(self):
        # now to give the root
        if self.dagtree.root is not None:
            headdag = self.dagtree.get_head_node(self.dagtree.root)
        else:
            return
        # now we should get the dag for bestchild get 

        retval = self.dagtree.check_best_child_as_head(headdag.idx)
        if not retval:
            sys.stderr.write('[%d] can not check head ok\n'%(self.dagtree.lindex))

        retval = self.check_attest(headdag.idx)
        return

DAG_EXPR_STR = '^(\\s*)(\\*)?\\[([0-9]+)\\]DagNode\\[Key\\s+([0-9a-fA-F]+)\\s+Slot\\s+([0-9a-fA-FxX]+)\\s+Height\\s+([0-9a-fA-FxX]+)\\s+Weight\\s+([0-9a-fA-FxX]+)\\s+Proposer\\s+([0-9a-fA-FxX]+)(\\s+Parent\\.Key\\s+([0-9a-f]+))?\\]\\s+bestchild\\s+([^ ]+)\\s+weight\\s+([0-9]+)\\s+besttarget\\s([0-9]+)$'
ATT_EXPR_STR = '^\\[([0-9]+)\\]\\s+Attestation\\[BeaconBlockRoot\\s+([a-f0-9A-F]+)\\s+ValidatorID\\s+([0-9a-fx]+)\\s+Weight\\s+([0-9a-fx]+)\\]$'

class ParseScoreChanges(object):
    def __init__(self):
        self.scorechanges = []
        return

    def parse(self,lindex,sarr):
        passed = lindex
        scoreexpr = re.compile(APPLYCHANGE_SCORECHANGE_EXPR_STR)
        while passed < len(sarr):
            l = sarr[passed]
            l = l.rstrip('\r\n')
            m = scoreexpr.findall(l)
            if m is None or len(m) == 0 or len(m[0]) < 8:
                return passed
            key = m[0][0]
            slot = parse_int(m[0][1])
            validatorid = parse_int(m[0][4])
            score = parse_int(m[0][7])

            curscore = ScoreChange()
            curscore.set_lindex(passed)
            curscore.set_slot(slot)
            curscore.set_key(key)
            curscore.set_score(score)
            curscore.set_validatorid(validatorid)
            self.scorechanges.append(curscore)
            passed += 1
        return passed

class ParseAttMap(object):
    def __init__(self):
        self.attmap = None
        return

    def parse(self,lindex,lines):
        passed = lindex
        attexpr = re.compile(ATT_EXPR_STR)
        while passed < len(lines):
            l = lines[passed]
            l = l.rstrip('\r\n')
            m = attexpr.findall(l)
            if m is None or len(m) == 0 or len(m[0]) < 4:
                return passed
            if self.attmap is None:
                self.attmap = LmdAttestMap(lindex)
            curatt = LmdAttest()
            validatorid = parse_int(m[0][2])
            key = m[0][1]
            weight = parse_int(m[0][3])
            curatt.set_attest(key,weight,validatorid)
            curatt.set_lindex(passed)
            self.attmap.set_node(curatt.validatorid,curatt)
            passed += 1
        return passed

class ParseDagNodeTree(object):
    def __init__(self):
        self.dagtree = None
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

    def parse(self,lindex,lines):
        passed = lindex
        dagpushs = []
        dagexpr = re.compile(DAG_EXPR_STR)
        self.dagtree = None
        while passed < len(lines):
            l = lines[passed]
            l = l.rstrip('\r\n')
            m = dagexpr.findall(l)
            if m is None or len(m) == 0 or len(m[0]) < 13:
                dagpushs = []
                return passed
            tabs = self._calc_tabs(m[0][0])
            ishead = False
            if m[0][1] == '*':
                ishead = True
            idx = parse_int(m[0][2])
            key = m[0][3]
            slot = parse_int(m[0][4])
            weight = parse_int(m[0][11])
            if m[0][10] == 'nonExistentNode':
                bestchild = -1
            else:
                bestchild = parse_int(m[0][10])
            besttarget = parse_int(m[0][12])
            # now to check the best                
            parent = None
            if True:
                if tabs >= len(dagpushs):
                    if len(dagpushs) > 0:
                        parent = dagpushs[-1]
                    dagpushs.append(key)
                else:
                    if tabs == (len(dagpushs) - 1):
                        if len(dagpushs) > 1:
                            parent = dagpushs[-2]
                        if len(dagpushs) > 0:
                            dagpushs[-1]= key
                        else:
                            dagpushs.append(key)
                    else:
                        dagpushs = dagpushs[:(tabs)]
                        if len(dagpushs) > 0:
                            parent = dagpushs[-1]
                        dagpushs.append(key)
            curdag = LmdDagNode()
            curdag.set_node(lindex,idx,key,weight,besttarget,bestchild,slot,ishead,parent)
            if self.dagtree is None:
                self.dagtree = LmdDagTree(lindex)
            self.dagtree.set_node(key,curdag)
            self.dagtree.set_index_node(idx,key)
            self.dagtree.set_child(parent,key)
            passed += 1
        return passed


class ParseDagNode(object):
    def __init__(self):
        self.dagnode = None
        return

    def parse(self,lindex,sarr):
        passed = lindex
        expr = re.compile(NEWNODE_DAG_EXPR_STR)
        m = expr.findall(sarr[passed])
        if m is None or len(m) == 0 or len(m[0]) < 7:
            return passed
        key = m[0][0]
        slot = parse_int(m[0][1])
        height = parse_int(m[0][2])
        weight = parse_int(m[0][3])
        validatorid = parse_int(m[0][4])
        parent = None
        if len(m[0][6]) != 0:
            parent = m[0][6]
        if self.dagnode is None:
            self.dagnode = DagNode()
        self.dagnode.set_lindex(lindex)
        self.dagnode.set_key(key)
        self.dagnode.set_height(height)
        self.dagnode.set_weight(weight)
        self.dagnode.set_validatorid(validatorid)
        self.dagnode.set_parent(parent)
        passed += 1
        return passed


NEXT_ATT_EXPR_STR = '.*\\s+agor$'
NEXT_DAG_EXPR_STR = '.*\\s+HeadFn$'

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
    def parse(self,verbosemode):
        ins = read_file(self.fname)
        if verbosemode == 0:
            sys.stdout.write('read [%s] %d buffer\n'%(self.fname,len(ins)))
        sarr = re.split('\n',ins)
        if verbosemode == 0:
            sys.stdout.write('read [%s] %d lines\n'%(self.fname,len(sarr)))
        nextattexpr = re.compile(NEXT_ATT_EXPR_STR)
        nextdagexpr = re.compile(NEXT_DAG_EXPR_STR)
        isatt = False
        isdag = False
        curdagtree = None
        curatttree = None
        curpair = None
        dagpushs = []
        lindex = 0
        progressout = ''
        lastlindex = 0
        stepcnt = 5000
        while lindex < len(sarr):
            l = sarr[lindex]
            if int(lastlindex / stepcnt) != int(lindex / stepcnt):
                if verbosemode == 0:
                    if sys.stdout.isatty():
                        if len(progressout) > 0:
                            idx = 0
                            while idx < len(progressout):
                                sys.stdout.write('\b')
                                idx += 1
                            idx = 0
                            while idx < len(progressout):
                                sys.stdout.write(' ')
                                idx += 1
                            idx = 0
                            while idx < len(progressout):
                                sys.stdout.write('\b')
                                idx += 1
                        progressout = 'process %d'%(lindex)
                        sys.stdout.write('%s'%(progressout))
                        sys.stdout.flush()
                lastlindex = lindex
            l = l.rstrip('\n\r')
            if not isatt and not isdag:
                if nextattexpr.match(l):
                    curatttree = ParseAttMap()
                    lindex = curatttree.parse(lindex+1,sarr)
                    isatt = False
                    continue
                if nextdagexpr.match(l):
                    isdag = True
                    curdagtree = ParseDagNodeTree()
                    lindex = curdagtree.parse(lindex+1,sarr)
                    if curatttree is not None and curatttree.attmap is not None and curdagtree.dagtree is not None:
                        lmdpair = LmdPair()
                        lmdpair.set_pair(curdagtree.dagtree,curatttree.attmap)
                        self.pairs.append(lmdpair)
                    curatttree = None
                    curdagtree = None
                    isdag = False
                    continue
            lindex += 1
        return

    def check_pair(self):
        idx = 0
        while idx < len(self.pairs):
            self.pairs[idx].check_pair()
            idx += 1
        return


class EvmRun(object):
    def __init__(self):
        self.protoarray = None
        self.atttree = None
        self.dagtree = None
        return

    def apply_protoarray(self,protoarray):
        if self.protoarray is None:
            self.protoarray = protoarray.deep_copy()
            return True
        retval = False
        try:
            self.protoarray.eq_op(protoarray,True)
            retval = True
        except:
            logging.error('%s'%(traceback.format_exc()))
        return retval

    def apply_score_change(self,scorechange):
        if self.protoarray is None:
            # nothing to apply
            return True
        # now to set the score change 
        return True

    def apply_new_node(self,node):
        if self.protoarray is None:
            return True
        # now to append the block
        sidx = len(self.protoarray.nodes)
        self.protoarray.indices[node.key] = sidx
        self.protoarray.bestchilds.append(-1)
        self.protoarray.weights.append(0)

        if node.parent is None:
            self.protoarray.parents.append(-1)
        else:
            if node.parent in self.protoarray.indices.keys():
                pi = self.protoarray.indices[node.parent]
                self.protoarray.parents.append(pi)
                if self.protoarray.bestchilds[pi] == -1:
                    self.protoarray.bestchilds[pi] = sidx
            else:
                self.protoarray.parents.append(-1)
        return True

    def apply_att_map(self,attmap):
        return True

    def apply_dag_tree(self,dagtree):
        return True



class ProcessChange(object):
    def __init__(self,fname):
        self.fname = fname
        self.procs = []
        return

    def parse(self,verbosemode=0):
        self.procs = []
        ins = read_file(self.fname)
        if verbosemode == 0:
            sys.stdout.write('read [%s] %d buffer\n'%(self.fname,len(ins)))
        sarr = re.split('\n',ins)
        if verbosemode == 0:
            sys.stdout.write('read [%s] %d lines\n'%(self.fname,len(sarr)))
        nextattexpr = re.compile(NEXT_ATT_EXPR_STR)
        nextdagexpr = re.compile(NEXT_DAG_EXPR_STR)
        isatt = False
        isdag = False
        dagexpr = re.compile(DAG_EXPR_STR)
        attexpr = re.compile(ATT_EXPR_STR)
        curdagtree = None
        curatttree = None
        lindex = 0
        progressout = ''
        lastlindex = 0
        stepcnt = 5000
        newnodeexpr = re.compile(NEWNODE_DAG_EXPR_STR)
        scoreexpr = re.compile(APPLYCHANGE_SCORECHANGE_EXPR_STR)
        while lindex < len(sarr):
            l = sarr[lindex]
            if int(lastlindex / stepcnt) != int(lindex / stepcnt):
                if verbosemode == 0:
                    if sys.stdout.isatty():
                        if len(progressout) > 0:
                            idx = 0
                            while idx < len(progressout):
                                sys.stdout.write('\b')
                                idx += 1
                            idx = 0
                            while idx < len(progressout):
                                sys.stdout.write(' ')
                                idx += 1
                            idx = 0
                            while idx < len(progressout):
                                sys.stdout.write('\b')
                                idx += 1
                        progressout = 'process %d'%(lindex)
                        sys.stdout.write('%s'%(progressout))
                        sys.stdout.flush()
                lastlindex = lindex
            l = l.rstrip('\n\r')

            if nextattexpr.match(l):
                curatttree = ParseAttMap()
                lindex = curatttree.parse(lindex+1,sarr)
                if curatttree.attmap is not None:
                    self.procs.append(curatttree.attmap)
                curatttree = None
                continue
            if nextdagexpr.match(l):
                curdagtree = ParseDagNodeTree()
                lindex = curdagtree.parse(lindex+1,sarr)
                if curdagtree.dagtree is not None:
                    self.procs.append(curdagtree.dagtree)
                curdagtree = None
                continue

            if newnodeexpr.match(l):
                curdagnode = ParseDagNode()
                lindex = curdagnode.parse(lindex,sarr)
                if curdagnode.dagnode is not None:
                    self.procs.append(curdagnode.dagnode)
                continue

            if scoreexpr.match(l):
                curscore = ParseScoreChanges()
                lindex = curscore.parse(lindex,sarr)
                self.procs.extend(curscore.scorechanges)
                continue
            lindex += 1
        return

    def check_run(self):
        idx = 0
        evm = EvmRun()
        while idx < len(self.procs):
            curobj = self.procs[idx]
            if isinstance(curobj,LmdAttest):
                retval = evm.apply_att_map(curobj)
            elif isinstance(curobj,LmdDagTree):
                retval = evm.apply_dag_tree(curobj)
            elif isinstance(curobj,DagNode):
                retval = evm.apply_new_node(curobj)
            elif isinstance(curobj,ScoreChange):
                retval = evm.apply_score_change(curobj)
            elif isinstance(curobj,ParseProtoArray):
                retval = evm.apply_protoarray(curobj)
            else:
                raise Exception('unknow type of curobj %s'%(curobj))
            if not retval:
                logging.error('run error on [%d] object'%(curobj.lindex))
            idx += 1







def lmdfilter_handler(args,parser):
    set_logging(args)
    lmdfilter = LmdFilter(args.input)
    lmdfilter.parse(args.verbose)
    lmdfilter.check_pair()
    sys.exit(0)

def applychange_handler(args,parser):
    set_logging(args)
    sys.exit(0)
    return

def load_base_parser(parser):
    commandline_fmt='''
    {
        "input|i" : null,
        "output|o" : null,
        "lmdfilter<%s.lmdfilter_handler>##to filter lmd struct from input as output by %s##" : {
            "$" : 0
        },
        "applychange<%s.applychange_handler>##to give the apply change from input as output by %s##" : {
            "$" : 0
        }
    }
    '''
    lmdfile = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','testing','lmd-ghost','lmd-ghost'))
    if is_windows():
        lmdfile = lmdfile.replace('\\','\\\\')
    commandline = commandline_fmt%(__name__,lmdfile,__name__,lmdfile)
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