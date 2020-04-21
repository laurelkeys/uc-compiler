import os
import sys

from uC_AST import NodeVisitor
from uC_types import *

###########################################################
## uC Semantics ###########################################
###########################################################

class SymbolTable(object):
    ''' Class representing a symbol table.\n
        It should provide functionality for adding and looking up nodes associated with identifiers. '''

    def __init__(self):
        self.symtab = {} # symbol table

    def lookup(self, a):
        return self.symtab.get(a)

    def add(self, a, v):
        self.symtab[a] = v


class Visitor(NodeVisitor):
    ''' Program visitor class.\n

        It flattens an uC program into a sequence of SSA code instructions, represented as tuples of the form:
        `(operation, operands, ..., destination)`\n

        Note: This class uses the visitor pattern.
        You need to define `visit_<>` methods for each kind of AST node that you want to process, where `<>` is the node name.
    '''

    def __init__(self):
        self.symtab = SymbolTable()
        # add built-in type names to the symbol table
        self.symtab.add("int", IntType)
        self.symtab.add("float", FloatType)
        self.symtab.add("char", CharType)
        self.symtab.add("void", VoidType)

    # NOTE A few sample methods follow. You may have to adjust
    #      depending on the names of the AST nodes you've defined

    def visit_Program(self, node):
        # 1. Visit all of the global declarations
        # 2. Record the associated symbol table
        for _decl in node.gdecls:
            self.visit(_decl)

    def visit_BinaryOp(self, node):
        # 1. Make sure left and right operands have the same type
        # 2. Make sure the operation is supported
        # 3. Assign the result type
        self.visit(node.left)
        self.visit(node.right)
        node.type = node.left.type

    def visit_Assignment(self, node):
        # 1. Make sure the location of the assignment is defined
        sym = self.symtab.lookup(node.location)
        assert sym, "Assigning to unknown sym"
        # 2. Check that the types match
        self.visit(node.value)
        assert sym.type == node.value.type, "Type mismatch in assignment"

    # TODO Implement `visit_<>` methods for all of the other AST nodes.
