import os
import sys

from uC_AST import *
from uC_ops import *
from uC_types import (TYPE_array, TYPE_bool, TYPE_char, TYPE_float, TYPE_int,
                      TYPE_string, TYPE_void)

###########################################################
## uC Semantic Analysis ###################################
###########################################################

class SymbolTable:
    ''' Class representing a symbol table.\n
        It should provide functionality for adding and looking up nodes associated with identifiers.
    '''

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
        self.symtab.add("int", TYPE_int)
        self.symtab.add("float", TYPE_float)
        self.symtab.add("char", TYPE_char)
        self.symtab.add("string", TYPE_string)
        self.symtab.add("bool", TYPE_bool)
        self.symtab.add("void", TYPE_void)
        self.symtab.add("array", TYPE_array)
        # TODO should we add built-in functions as well (e.g. read, assert, etc.)?

    def visit_ArrayDecl(self, node: ArrayDecl): # [type*, dim*]
        raise NotImplementedError

    def visit_ArrayRef(self, node: ArrayRef): # [name*, subscript*]
        raise NotImplementedError

    def visit_Assert(self, node: Assert): # [expr*]
        self.visit(node.expr)
        assert node.expr.type == TYPE_bool, f"No implementation for: `assert {node.expr.type}`"

    def visit_Assignment(self, node: Assignment): # [op, lvalue*, rvalue*]
        sym = self.symtab.lookup(node.lvalue)
        assert sym is None, f"Assignment to unknown lvalue `{node.lvalue}`"
        self.visit(node.rvalue)

        _str = _Assignment_str(node)
        _ltype, _rtype = node.lvalue.type, node.rvalue.type
        assert _ltype == _rtype, f"Type mismatch: `{_str}`"
        node.type = _ltype

    def visit_BinaryOp(self, node: BinaryOp): # [op, left*, right*]
        self.visit(node.left)
        self.visit(node.right)

        _str = _BinaryOp_str(node)
        _ltype, _rtype = node.left.type, node.right.type
        assert _ltype == _rtype, f"Type mismatch: `{_str}`"
        node.type = _ltype

        _type_ops = node.left.type.binary_ops
        assert binary_ops[node.op] in _type_ops, f"Operation not supported by type {_ltype}: `{_str}`"

    def visit_Break(self, node: Break): # []
        pass

    def visit_Cast(self, node: Cast): # [type*, expr*]
        raise NotImplementedError

    def visit_Compound(self, node: Compound): # [decls**, stmts**]
        raise NotImplementedError

    def visit_Constant(self, node: Constant): # [type, value]
        raise NotImplementedError

    def visit_Decl(self, node: Decl): # [name, type*, init*]
        raise NotImplementedError

    def visit_DeclList(self, node: DeclList): # [decls**]
        raise NotImplementedError

    def visit_EmptyStatement(self, node: EmptyStatement): # []
        pass

    def visit_ExprList(self, node: ExprList): # [exprs**]
        raise NotImplementedError

    def visit_For(self, node: For): # [init*, cond*, next*, body*]
        raise NotImplementedError

    def visit_FuncCall(self, node: FuncCall): # [name*, args*]
        raise NotImplementedError

    def visit_FuncDecl(self, node: FuncDecl): # [args*, type*]
        if node.args is not None:
            for arg in node.args:
                self.visit(arg)
        self.visit(node.type)

    def visit_FuncDef(self, node: FuncDef): # [spec*, decl*, param_decls**, body*]
        raise NotImplementedError

    def visit_GlobalDecl(self, node: GlobalDecl): # [decls**]
        raise NotImplementedError

    def visit_ID(self, node: ID): # [name]
        raise NotImplementedError

    def visit_If(self, node: If): # [cond*, ifthen*, ifelse*]
        raise NotImplementedError

    def visit_InitList(self, node: InitList): # [exprs**]
        for expr in node.exprs:
            self.visit(expr)

    def visit_ParamList(self, node: ParamList): # [params**]
        for param in node.params:
            self.visit(param)

    def visit_Print(self, node: Print): # [expr*]
        self.visit(node.expr)

    def visit_Program(self, node: Program): # [gdecls**]
        for gdecl in node.gdecls:
            self.visit(gdecl)

    def visit_PtrDecl(self, node: PtrDecl): # [type*]
        raise NotImplementedError

    def visit_Read(self, node: Read): # [expr*]
        self.visit(node.expr)

    def visit_Return(self, node: Return): # [expr*]
        self.visit(node.expr)

    def visit_Type(self, node: Type): # [names]
        raise NotImplementedError

    def visit_VarDecl(self, node: VarDecl): # [declname, type*]
        raise NotImplementedError

    def visit_UnaryOp(self, node: UnaryOp): # [op, expr*]
        self.visit(node.expr)
        node.type = node.expr.type

        _str = _UnaryOp_str(node)
        _type = node.expr.type
        _type_ops = node.expr.type.unary_ops
        assert unary_ops[node.op] in _type_ops, f"Operation not supported by type {_type}: `{_str}`"

    def visit_While(self, node: While): # [cond*, body*]
        raise NotImplementedError


# Helper functions for error printing
def _Assignment_str(node):
    return f"{node.lvalue.type} {assign_ops[node.op]} {node.rvalue.type}"

def _BinaryOp_str(node):
    return f"{node.left.type} {binary_ops[node.op]} {node.right.type}"

def _UnaryOp_str(node):
    if node.op[0] == 'p': # suffix/postfix increment and decrement
        return f"{node.expr.type}{unary_ops[node.op][1:]}"
    return f"{unary_ops[node.op]}{node.expr.type}"
