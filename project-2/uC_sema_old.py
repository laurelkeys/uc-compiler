import os
import sys

from collections import ChainMap

import uC_types

from uC_AST import *
from uC_ops import *
from uC_types import (TYPE_ARRAY, TYPE_BOOL, TYPE_CHAR, TYPE_FLOAT, TYPE_FUNC,
                      TYPE_INT, TYPE_STRING, TYPE_VOID)

###########################################################
## uC Semantic Analysis ###################################
###########################################################

class Scope:
    def __init__(self, kind: str, name: str, node: str):
        assert kind in ["global", "local", "func", "loop"]
        self.kind = kind
        self.name = name
        self.node = node

class SymbolTable:
    ''' Class representing a symbol table.\n
        It should provide functionality for adding and looking up nodes associated with identifiers.
    '''

    def __init__(self, global_scope=None):
        self.symbol_table = ChainMap() if global_scope is None else ChainMap(global_scope)
        self.loops = [] # list of loops that wrap the current scope
        self.funcs = [] # list of funcs that wrap the current scope

    @property
    def in_loop(self): return not self.loops # return any(scope.kind == "loop" for scope in self.scope_stack)
    @property
    def in_func(self): return not self.funcs # return any(scope.kind == "func" for scope in self.scope_stack)

    # NOTE maybe use in_* to refer to the current scope (self.scope_stack[-1]) and wrapped_by_* to search all

    @property
    def curr_loop(self): return self.loops[-1]
    @property
    def curr_func(self): return self.funcs[-1]

    def add(self, name: str, value: Node):
        ''' Inserts a node with attributes (`value.attrs`) associated to `name` in the current scope. '''
        assert isinstance(name, str), f"expected str, received type {type(name)}: {name}"
        self.symbol_table[name] = value

    def lookup(self, name: str):
        ''' Returns the node with attributes associated to `name` if it exists, otherwise `None`. '''
        assert isinstance(name, str), f"expected str, received type {type(name)}: {name}"
        return self.symbol_table.get(name, None)

    def begin_scope(self, loop: Node = None, func: Node = None):
        ''' Push a new symbol table, generating a new (current) scope.\n
            If `loop`/`func` is not `None`, it becomes the `curr_loop`/`curr_func`.
        '''
        self.symbol_table = self.symbol_table.new_child()
        if loop is not None: self.loops.append(loop)
        if func is not None: self.funcs.append(func)

    def end_scope(self, loop: bool = False, func: bool = False):
        ''' Pop the current scope's symbol table, effectively deleting it.\n
            If `loop`/`func` is `True`, the `curr_loop`/`curr_func` is also popped.
        '''
        self.symbol_table = self.symbol_table.parents
        if loop: self.loops.pop()
        if func: self.funcs.pop()

    @property
    def current_scope(self): return self.symbol_table # contains everything that's currently visible
    @property
    def global_scope(self): return self.symbol_table.maps[-1]
    @property
    def local_scope(self): return self.symbol_table.maps[0]

    def __str__(self):
        return str(self.symbol_table)


class Visitor(NodeVisitor):
    ''' Program visitor class.\n

        It flattens an uC program into a sequence of SSA code instructions, represented as tuples of the form:
        `(operation, operands, ..., destination)`\n

        Note: This class uses the visitor pattern.
        You need to define `visit_<>` methods for each kind of AST node that you want to process, where `<>` is the node name.
    '''

    def __init__(self):
        self.symtab = SymbolTable({
            # built-in types
            "int": TYPE_INT,
            "float": TYPE_FLOAT,
            "char": TYPE_CHAR,
            "string": TYPE_STRING,
            "void": TYPE_VOID,
            # semantic types
            "array": TYPE_ARRAY,
            "bool": TYPE_BOOL,
            "func": TYPE_FUNC,
            #"ptr": TYPE_PTR,
        })

    # TODO put UCType into the result of BinaryOp, UnaryOp, Assignment, ... (any other?)
    # TODO add name to symtab on visit_.*Decl

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
        assert isinstance(node.name, ID)

        self.visit(node.name)
        assert node.name.name in self.symtab.current_scope, (
            f"Reference to undeclared array `{node.name.name}`"
        )

        self.visit(node.subscript)
        # TODO if isinstance(node.subscript, ID) assert it's in scope
        assert node.subscript._uctype == TYPE_INT, (
            f"Array indexed with non-integer type: {node.subscript._uctype}"
        )

    def visit_Assert(self, node: Assert): # [expr*]
        self.visit(node.expr)
        assert node.expr._uctype == TYPE_BOOL, f"No implementation for: `assert {node.expr.type}`"

    def visit_Assignment(self, node: Assignment): # [op, lvalue*, rvalue*]
        # FIXME this might be dealt with by visit_ID
        assert isinstance(node.lvalue, ID), (
            f"Assignment to invalid lvalue `{node.lvalue}`"
        )
        assert node.lvalue in self.symtab.current_scope, (
            f"Assignment to unknown lvalue `{node.lvalue}`"
        )
        if isinstance(node.rvalue, (ID, FuncCall)):
            assert node.rvalue in self.symtab.current_scope, (
                f"Assignment of unknown rvalue: `{node.lvalue}` = `{node.rvalue}`"
            )
        self.visit(node.lvalue)
        self.visit(node.rvalue)

        _str = _Assignment_str(node)
        _ltype, _rtype = node.lvalue._uctype, node.rvalue._uctype # FIXME
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
        assert self.symtab.in_loop, f"Invalid call of break outside of any loop"

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

        assert node.name not in self.symtab.local_scope, f"Redeclaration of `{node.name}` in scope"

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

    def visit_EmptyStatement(self, node: EmptyStatement): # []
        pass

    def visit_ExprList(self, node: ExprList): # [exprs**]
        for expr in node.exprs:
            self.visit(expr)
            # TODO if expr is an ID, check if it's in scope

    def visit_For(self, node: For): # [init*, cond*, next*, body*]
        self.symtab.in_loop = True
        self.symtab.begin_scope()

        self.visit(node.init)
        self.visit(node.cond)
        self.visit(node.next)
        self.visit(node.body)

        self.symtab.end_scope()
        self.symtab.in_loop = False

    def visit_FuncCall(self, node: FuncCall): # [name*, args*]
        assert isinstance(node.name, ID)

        assert node.name.name in self.symtab.current_scope, (
            f"Function `{node.name.name}` has been called, but not defined"
        )

        # TODO check if name's type is actually a function
        # TODO check for correct number and type of arguments

        self.visit(node.name)
        self.visit(node.args)

    def visit_FuncDecl(self, node: FuncDecl): # [args*, type*]
        self.symtab.begin_scope(node) # NOTE this is closed at FuncDef

        self.visit(node.type)
        node.attrs['base_type'] = node.type.attrs['base_type']
        node.attrs['full_type'] = node.type.attrs['full_type']
        if node.args is not None:
            for arg in node.args:
                self.visit(arg)

    def visit_FuncDef(self, node: FuncDef): # [spec*, decl*, param_decls**, body*]
        self.symtab.in_func = True

        self.visit(node.spec)
        self.visit(node.decl)
        if node.param_decls is not None:
            for param in node.param_decls:
                self.visit(param)
        assert isinstance(node.body, Compound)
        self.visit(node.body)

        sym = self.symtab.lookup(node.decl.name.name)
        sym['defined?'] = True
        sym['declared?'] = False

        self.symtab.in_func = False
        self.symtab.end_scope() # NOTE this was opened at FuncDecl

    def visit_GlobalDecl(self, node: GlobalDecl): # [decls**]
        assert self.symtab.lookup("_scope") == "global"
        for decl in node.decls:
            self.visit(decl)

    def visit_ID(self, node: ID): # [name]
        #raise NotImplementedError
        pass

    def visit_If(self, node: If): # [cond*, ifthen*, ifelse*]
        self.symtab.begin_scope()

        self.visit(node.cond)
        # TODO check cond._uctype == TYPE_BOOL
        self.visit(node.ifthen)
        if node.ifelse is not None:
            self.visit(node.ifelse)

        self.symtab.end_scope()

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
        node.attrs['base_type'] = uC_types.from_name(node.names[-1])
        if len(node.names) > 1:
            node.attrs['full_type'] = [uC_types.from_name(name) for name in node.names]

    def visit_VarDecl(self, node: VarDecl): # [declname, type*]
        assert isinstance(node.declname, ID)
        node.attrs['name'] = node.declname.name

        self.visit(node.type)
        node.attrs['type'] = node.type.attrs['type']

        # TODO check if we should assert for some kind of type mismatch in here

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
        self.symtab.curr_loop = node
        self.symtab.begin_scope()

        self.visit(node.cond)
        # TODO check if the type of cond is BOOL_TYPE
        #      for this we first have to replace the .type
        #      values with UCType singletons from uC_types
        assert node.cond._uctype == TYPE_BOOL, (
            f"While condition does not evaluate to boolean: while ({node.cond._uctype})"
        )
        if node.body is not None:
            self.visit(node.body)

        self.symtab.end_scope()
        self.symtab.curr_loop = None


# Helper functions for error printing
def _Assignment_str(node):
    return f"{node.lvalue._uctype} {assign_ops[node.op]} {node.rvalue._uctype}"

def _BinaryOp_str(node):
    return f"{node.left._uctype} {binary_ops[node.op]} {node.right._uctype}"

def _UnaryOp_str(node):
    if node.op[0] == 'p': # suffix/postfix increment and decrement
        return f"{node.expr._uctype}{unary_ops[node.op][1:]}"
    return f"{unary_ops[node.op]}{node.expr._uctype}"
