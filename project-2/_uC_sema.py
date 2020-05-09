import os
import sys

from collections import ChainMap

import uC_ops
import uC_types

from uC_AST import *
from uC_types import (TYPE_INT, TYPE_FLOAT, TYPE_CHAR, TYPE_STRING, TYPE_VOID,
                      TYPE_ARRAY, TYPE_BOOL, TYPE_FUNC)

###########################################################
## uC Semantic Analysis ###################################
###########################################################

# ref.: https://en.cppreference.com/w/c/language/scope
class Scope:
    def __init__(self, kind: str, name: str, node: str):
        assert kind in ["global", "local", "func", "loop"]
        self.kind = kind
        self.name = name
        self.node = node

    # NOTE "global" is the whole (file) scope enclosed by a Program node
    #      "local" is a (block) scope delimited by an if-statement or by {}'s
    #      "func" is a function-local (block) scope delimited by a function declaration/definition
    #      "loop" is a loop-local (block) scope delimited by a for- or while-loop

class SymbolTable:
    ''' Class representing a symbol table.\n
        It should provide functionality for adding and looking up nodes associated with identifiers.
    '''

    def __init__(self):
        self.symbol_table = ChainMap()
        self.scope_stack = []

    @property
    def in_loop(self): return not self.loops # return any(scope.kind == "loop" for scope in self.scope_stack)
    @property
    def in_func(self): return not self.funcs # return any(scope.kind == "func" for scope in self.scope_stack)

    # NOTE maybe use in_* to refer to the current scope (self.scope_stack[-1]) and wrapped_by_* to search all

    @property
    def curr_loop(self): return self.loops[-1]
    @property
    def curr_func(self): return self.funcs[-1]

    def add(self, name: str, attributes):
        ''' Inserts `attributes` associated to `name` in the current scope. '''
        assert isinstance(name, str), f"expected str, received type {type(name)}: {name}"
        self.symbol_table[name] = attributes

    def lookup(self, name: str):
        ''' Returns the attributes associated to `name` if it exists, otherwise `None`. '''
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
        #return str(self.symbol_table)
        return (
            f"{self.__class__.__name__}(\n  "
            + ", \n  ".join([f"{k}={v}" for k, v in self.__dict__.items()])
            + "\n)"
        )


class Visitor(NodeVisitor):
    ''' Program visitor class.\n

        It flattens an uC program into a sequence of SSA code instructions, represented as tuples of the form:
        `(operation, operands, ..., destination)`\n

        Note: This class uses the visitor pattern.
        You need to define `visit_<>` methods for each kind of AST node that you want to process, where `<>` is the node name.
    '''

    def __init__(self):
        self.symtab = SymbolTable()

        self.symtab.symbol_table.update({
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

    def visit_ArrayDecl(self, node: ArrayDecl): # [type*, dim*]
        print("====>", type(node.type))
        print("====>", type(node.dim))
        sym_dim = None
        if node.dim is not None:
            self.visit(node.dim)
        #     if isinstance(node.dim, Constant):
        #         sym_dim = node.dim.attrs
        #     elif isinstance(node.dim, ID):
        #     else:
        #         assert False, str(type(node.dim)) # FIXME

        pass

    def visit_ArrayRef(self, node: ArrayRef): # [name*, subscript*]
        pass

    def visit_Assert(self, node: Assert): # [expr*]
        pass

    def visit_Assignment(self, node: Assignment): # [op, lvalue*, rvalue*]
        pass

    def visit_BinaryOp(self, node: BinaryOp): # [op, left*, right*]
        pass

    def visit_Break(self, node: Break): # []
        pass

    def visit_Cast(self, node: Cast): # [type*, expr*]
        pass

    def visit_Compound(self, node: Compound): # [decls**, stmts**]
        pass

    def visit_Constant(self, node: Constant): # [type, value]
        node.attrs['type'] = [uC_types.from_name(node.type)]
        node.attrs['value'] = node.value

    def visit_Decl(self, node: Decl): # [name, type*, init*]
        assert isinstance(node.name, ID)
        self.visit(node.name)
        sym_name = node.name.name
        assert sym_name not in self.symtab.local_scope, f"Redeclaration of `{sym_name}`"

        if isinstance(node.type, VarDecl):
            pass
        elif isinstance(node.type, ArrayDecl):
            pass
        elif isinstance(node.type, FuncDecl):
            pass
        else:
            assert False, f"Unexpected type {type(node.type)} for node.type"
        self.visit(node.type)
        sym_type = node.type.attrs['type']
        
        sym_value = None
        if node.init is not None:
            self.visit(node.init)
            assert node.init.attrs['type'] == sym_type, (
                f"Implicit conversions are not supported: {sym_type} = {node.init.attrs['type']}"
            )
            sym_value = node.init.attrs['value']

        self.symtab.add(
            name=sym_name,
            attributes={
                "type": sym_type,
                "value": sym_value,
                # TODO add scope
            } # FIXME add param info if FuncDecl
        )

    def visit_DeclList(self, node: DeclList): # [decls**]
        pass

    def visit_EmptyStatement(self, node: EmptyStatement): # []
        pass

    def visit_ExprList(self, node: ExprList): # [exprs**]
        pass

    def visit_For(self, node: For): # [init*, cond*, next*, body*]
        pass

    def visit_FuncCall(self, node: FuncCall): # [name*, args*]
        pass

    def visit_FuncDecl(self, node: FuncDecl): # [args*, type*]
        assert isinstance(node.type, VarDecl)
        self.visit(node.type)
        node.attrs['type'] = node.type.attrs['type']

        assert isinstance(node.type, ParamList) # FIXME maybe (?)
        self.visit(node.args)
        # TODO add param info to attrs

    def visit_FuncDef(self, node: FuncDef): # [spec*, decl*, param_decls**, body*]
        pass

    def visit_GlobalDecl(self, node: GlobalDecl): # [decls**]
        for decl in node.decls:
            self.visit(decl)

    def visit_ID(self, node: ID): # [name]
        pass

    def visit_If(self, node: If): # [cond*, ifthen*, ifelse*]
        pass

    def visit_InitList(self, node: InitList): # [exprs**]
        pass

    def visit_ParamList(self, node: ParamList): # [params**]
        param_types = []
        for param in node.params:
            self.visit(param)
            param_types.append(param.attrs['type'])
        node.attrs['param_types'] = param_types

    def visit_Print(self, node: Print): # [expr*]
        pass

    def visit_Program(self, node: Program): # [gdecls**]
        self.symtab.begin_scope()
        
        for gdecl in node.gdecls:
            assert isinstance(gdecl, (GlobalDecl, FuncDef))
            self.visit(gdecl)
        
        # self.symtab.end_scope()

    def visit_PtrDecl(self, node: PtrDecl): # [type*]
        pass

    def visit_Read(self, node: Read): # [expr*]
        pass

    def visit_Return(self, node: Return): # [expr*]
        pass

    def visit_Type(self, node: Type): # [names]
        node.attrs['type'] = [uC_types.from_name(name) for name in node.names]

    def visit_VarDecl(self, node: VarDecl): # [declname, type*]
        assert isinstance(node.type, Type)
        self.visit(node.type)
        node.attrs['type'] = node.type.attrs['type']

    def visit_UnaryOp(self, node: UnaryOp): # [op, expr*]
        pass

    def visit_While(self, node: While): # [cond*, body*]
        pass