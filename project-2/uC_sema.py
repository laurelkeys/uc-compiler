import os
import sys
sys.path.insert(0, os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/../project-1"
))

from uC_AST import NodeVisitor

###########################################################
## uC Semantics ###########################################
###########################################################

class SymbolTable(object):
    ''' Class representing a symbol table.\n
        It should provide functionality for adding and looking up nodes associated with identifiers. '''

    def __init__(self):
        self.symtab = {}

    def lookup(self, a):
        return self.symtab.get(a)

    def add(self, a, v):
        self.symtab[a] = v

class Visitor(NodeVisitor):
    ''' Program visitor class.\n
        This class uses the visitor pattern.
        You need to define `visit_<>` methods for each kind of AST node that you want to process, where `<>` is the node name.
    '''

    def __init__(self):
        # TODO