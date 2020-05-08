import os
import sys

from collections import ChainMap

from uC_AST import *
from uC_ops import *
from uC_types import (TYPE_ARRAY, TYPE_BOOL, TYPE_CHAR, TYPE_FLOAT, TYPE_INT,
                      TYPE_STRING, TYPE_VOID, from_typename)

###########################################################
## uC Semantic Analysis ###################################
###########################################################

class SymbolTable:
    ''' Class representing a symbol table.\n
        It should provide functionality for adding and looking up nodes associated with identifiers.
    '''

    def __init__(self):
        self.symtab = ChainMap()

    def add(self, name, value):
        self.symtab[name] = value

    def lookup(self, name):
        return self.symtab.get(name, None)

    def update(self, other):
        self.symtab.update(other)

    def begin_scope(self, node=None, **kwargs):
        # assert isinstance(node, (Program, FuncDef, For)) # , FuncCall, FuncDecl
        self.symtab = self.symtab.new_child()
        self.symtab.update(**kwargs)
        # TODO verify if node is needed

    def end_scope(self):
        self.symtab = self.symtab.parents

    def __str__(self):
        return str(self.symtab)


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
        self.symtab.update({
            "int": TYPE_INT,
            "float": TYPE_FLOAT,
            "char": TYPE_CHAR,
            "string": TYPE_STRING,
            "bool": TYPE_BOOL,
            "void": TYPE_VOID,
            "array": TYPE_ARRAY
        })
        self.symtab.begin_scope(_scope="global")

    # NOTE some functions have type assertions (i.e. assert isinstance),
    #      these will fail, just add the missing types to the assert as they appear :)

    # TODO put UCType into the result of BinaryOp, UnaryOp, Assignment, ... (any other?)

    def visit_ArrayDecl(self, node: ArrayDecl): # [type*, dim*]
        self.visit(node.type)

        _var_type = node.type # NOTE ArrayDecl is a type modifier
        while not isinstance(_var_type, VarDecl):
            _var_type = _var_type.type
        _var_type.type.names.insert(0, TYPE_ARRAY)

        if node.dim is not None:
            self.visit(node.dim)
            assert node.dim._uctype == TYPE_INT, (
                f"Array dimensions specified with non-integer type: {node.dim._uctype}"
            )

        node._uctype = TYPE_ARRAY

    def visit_ArrayRef(self, node: ArrayRef): # [name*, subscript*]
        self.visit(node.name)
        # TODO assert the name is in scope

        self.visit(node.subscript)
        # TODO if isinstance(node.subscript, ID) assert it's in scope
        assert node.subscript._uctype == TYPE_INT, (
            f"Array indexed with non-integer type: {node.subscript._uctype}"
        )


    def visit_Assert(self, node: Assert): # [expr*]
        self.visit(node.expr)
        assert node.expr._uctype == TYPE_BOOL, f"No implementation for: `assert {node.expr.type}`"

    def visit_Assignment(self, node: Assignment): # [op, lvalue*, rvalue*]
        sym = self.symtab.lookup(node.lvalue)
        assert sym is None, f"Assignment to unknown lvalue `{node.lvalue}`"
        self.visit(node.rvalue)

        _str = _Assignment_str(node)
        _ltype, _rtype = node.lvalue._uctype, node.rvalue._uctype
        assert _ltype == _rtype, f"Type mismatch: `{_str}`"
        node.type = _ltype

    def visit_BinaryOp(self, node: BinaryOp): # [op, left*, right*]
        self.visit(node.left)
        self.visit(node.right)

        # TODO add "bool" type for relational operators
        _str = _BinaryOp_str(node)
        _ltype, _rtype = node.left.type, node.right.type # FIXME we may need to compare .names[-1]
        assert _ltype == _rtype, f"Type mismatch: `{_str}`"
        node.type = _ltype

        _type_ops = node.left.type.binary_ops
        assert binary_ops[node.op] in _type_ops, f"Operation not supported by type {_ltype}: `{_str}`"

    def visit_Break(self, node: Break): # []
        # TODO check we're currently inside a loop and bind the node with it
        pass

    def visit_Cast(self, node: Cast): # [type*, expr*]
        # TODO should we check if the conversion is valid ?
        self.visit(node.type)
        self.visit(node.expr)
        node._uctype = from_typename(node.type.names[-1]) # FIXME check 23-04 topright

    def visit_Compound(self, node: Compound): # [decls**, stmts**]
        if node.decls is not None:
            for decl in node.decls:
                self.visit(decl)
        if node.stmts is not None:
            for stmt in node.stmts:
                self.visit(stmt)

    def visit_Constant(self, node: Constant): # [type, value]
        # TODO convert node.type from string name to UCType
        #raise NotImplementedError
        pass

    def visit_Decl(self, node: Decl): # [name, type*, init*]
        assert isinstance(node.type, (VarDecl, ArrayDecl, PtrDecl, FuncDecl))

        # FIXME check if we need a special check for FuncDecl

        if self.symtab.lookup(node.name) is not None:
            assert node.name not in self.symtab.symtab.parents, f"Redeclaration of `{node.name}`"

        self.visit(node.type)
        if node.init is not None:
            self.visit(node.init)
            assert node.type._uctype == node.init._uctype, (
                f"Type mismatch for `{node.name}`: `{node.type._uctype}` = `{node.init._uctype}`"
            )

        node._uctype = node.type._uctype
        self.symtab.add(node.name, value=node)

    def visit_DeclList(self, node: DeclList): # [decls**]
        for decl in node.decls:
            self.visit(decl)
        # TODO is there anything else to do in here ?()
        #raise NotImplementedError
        pass

    def visit_EmptyStatement(self, node: EmptyStatement): # []
        pass

    def visit_ExprList(self, node: ExprList): # [exprs**]
        for expr in node.exprs:
            self.visit(expr)
            # TODO if expr is an ID, check if it's in scope

    def visit_For(self, node: For): # [init*, cond*, next*, body*]
        if isinstance(node.init, DeclList):
            # NOTE these values declared should only be visible inside the for-loop
            self.symtab.begin_scope(node)

        # TODO add some kind of curr_loop to be used by Break to
        #      bind itself to the For for easier code generation
        self.visit(node.init)
        self.visit(node.cond)
        self.visit(node.next)
        self.visit(node.body)

        if isinstance(node.init, DeclList):
            self.symtab.end_scope()

    def visit_FuncCall(self, node: FuncCall): # [name*, args*]
        #raise NotImplementedError
        pass

    def visit_FuncDecl(self, node: FuncDecl): # [args*, type*]
        # TODO add this function to symtab
        self.visit(node.type)
        if node.args is not None:
            for arg in node.args:
                self.visit(arg)

    def visit_FuncDef(self, node: FuncDef): # [spec*, decl*, param_decls**, body*]
        # TODO check if begin_scope should be done at visit_FuncDecl
        self.symtab.begin_scope(node)

        self.visit(node.spec)
        self.visit(node.decl)
        if node.param_decls is not None:
            for param in node.param_decls:
                self.visit(param)
        assert isinstance(node.body, Compound)
        self.visit(node.body)

        self.symtab.end_scope()

    def visit_GlobalDecl(self, node: GlobalDecl): # [decls**]
        assert self.symtab.lookup("_scope") == "global"
        for decl in node.decls:
            self.visit(decl)

    def visit_ID(self, node: ID): # [name]
        #raise NotImplementedError
        pass

    def visit_If(self, node: If): # [cond*, ifthen*, ifelse*]
        self.visit(node.cond)
        # TODO check cond._uctype == TYPE_BOOL
        self.visit(node.ifthen)
        if node.ifelse is not None:
            self.visit(node.ifelse)

    def visit_InitList(self, node: InitList): # [exprs**]
        for expr in node.exprs:
            self.visit(expr)

    def visit_ParamList(self, node: ParamList): # [params**]
        for param in node.params:
            self.visit(param)

    def visit_Print(self, node: Print): # [expr*]
        if node.expr is not None:
            assert isinstance(node.expr, ExprList)
            for expr in node.expr:
                self.visit(node.expr)

    def visit_Program(self, node: Program): # [gdecls**]
        self.symtab.begin_scope(node)
        for gdecl in node.gdecls:
            assert isinstance(gdecl, (GlobalDecl, FuncDef))
            self.visit(gdecl)
        self.symtab.end_scope()

    def visit_PtrDecl(self, node: PtrDecl): # [type*]
        # self.visit(node.type)
        # basic_type = node.type
        # while not isinstance(type, VarDecl):
        #     basic_type = basic_type.type
        # basic_type.type.names.insert(0, TYPE_PTR)
        #raise NotImplementedError
        pass

    def visit_Read(self, node: Read): # [expr*]
        assert isinstance(node.expr, ExprList)
        for expr in node.expr:
            self.visit(node.expr)

    def visit_Return(self, node: Return): # [expr*]
        self.visit(node.expr)

    def visit_Type(self, node: Type): # [names]
        #raise NotImplementedError
        pass

    def visit_VarDecl(self, node: VarDecl): # [declname, type*]
        #raise NotImplementedError
        pass

    def visit_UnaryOp(self, node: UnaryOp): # [op, expr*]
        self.visit(node.expr)
        _source = node.expr.gen_location

        #if node.op == '&': # get the reference
        #    node.gen_location = node.expr.gen_location
        #elif node.op == '*':
        #    pass
        #node.type = node.expr.type
        # TODO check 23-04 bottomright
        
        # FIXME might need ._uctype below
        _str = _UnaryOp_str(node)
        _type = node.expr.type
        _type_ops = node.expr.type.unary_ops 
        assert unary_ops[node.op] in _type_ops, f"Operation not supported by type {_type}: `{_str}`"

    def visit_While(self, node: While): # [cond*, body*]
        self.visit(node.cond)
        # TODO check if the type of cond is BOOL_TYPE
        #      for this we first have to replace the .type
        #      values with UCType singletons from uC_types
        assert node.cond._uctype == TYPE_BOOL, (
            f"While condition does not evaluate to boolean: while ({node.cond._uctype})"
        )
        if node.body is not None:
            self.visit(node.body)


# Helper functions for error printing
def _Assignment_str(node):
    return f"{node.lvalue._uctype} {assign_ops[node.op]} {node.rvalue._uctype}"

def _BinaryOp_str(node):
    return f"{node.left._uctype} {binary_ops[node.op]} {node.right._uctype}"

def _UnaryOp_str(node):
    if node.op[0] == 'p': # suffix/postfix increment and decrement
        return f"{node.expr._uctype}{unary_ops[node.op][1:]}"
    return f"{unary_ops[node.op]}{node.expr._uctype}"
