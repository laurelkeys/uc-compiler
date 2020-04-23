import os
import sys

from uC_AST import NodeVisitor
from uC_ops import *
from uC_types import (array_type, bool_type, char_type, float_type, int_type,
                      string_type, void_type)

###########################################################
## uC Semantics ###########################################
###########################################################

class SymbolTable(object):
    ''' Class representing a symbol table.\n
        It should provide functionality for adding and looking up nodes associated with identifiers. '''

    def __init__(self):
        self.symtab = {} # symbol table

    def lookup(self, a):
        return self.symtab.get(a, None)

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
        self.symtab.add("int", int_type)
        self.symtab.add("float", float_type)
        self.symtab.add("char", char_type)
        self.symtab.add("string", string_type)
        self.symtab.add("bool", bool_type)
        self.symtab.add("void", void_type)
        self.symtab.add("array", array_type)
        # TODO should we add built-in functions as well (e.g. read, assert, etc.)?

    # NOTE A few sample methods follow. You may have to adjust
    #      depending on the names of the AST nodes you've defined

    def visit_Program(self, node):
        for gdecl in node.gdecls:
            self.visit(gdecl)

    def visit_ArrayDecl(self, node):
        raise NotImplementedError

    def visit_Assignment(self, node):
        sym = self.symtab.lookup(node.lvalue)
        assert sym, f"Assignment to unknown lvalue `{node.lvalue}`"

        self.visit(node.rvalue)
        assert sym.type == node.rvalue.type, f"Type mismatch: {_Assignment_str(node)}"

    def visit_BinaryOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

        _str = _BinaryOp_str(node)
        _ltype, _rtype = node.left.type, node.right.type
        assert _ltype == _rtype, f"Type mismatch: {_str}"
        node.type = _ltype

        _ltype_ops, _rtype_ops = node.left.type.binary_ops, node.right.type.binary_ops
        assert node.op in _ltype_ops, f"Operation not supported by type {_ltype}: {_str}"
        assert node.op in _rtype_ops, f"Operation not supported by type {_rtype}: {_str}"

    # TODO Implement `visit_<>` methods for all of the other AST nodes.


# Helper functions for error printing
def _Assignment_str(node):
    return f"`{node.lvalue.type} {assign_ops[node.op]} {node.rvalue.type}`"

def _BinaryOp_str(node):
    return f"`{node.left.type} {binary_ops[node.op]} {node.right.type}`"

def _UnaryOp_str(node):
    if node.op[0] == 'p': # suffix/postfix increment and decrement
        return f"`{node.expr.type}{unary_ops[node.op][1:]}`"
    return f"`{unary_ops[node.op]}{node.expr.type}`"
