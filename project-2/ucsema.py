import os
import sys

from collections import ChainMap

from uC_AST import *
from uC_ops import *
from uC_types import (TYPE_ARRAY, TYPE_BOOL, TYPE_CHAR, TYPE_FLOAT, TYPE_INT,
                      TYPE_STRING, TYPE_VOID, str2uctype)

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

class Environment:
    # 16-04 bottom
    # 30-04

    pass

class Visitor(NodeVisitor):
    ''' Program visitor class.\n

        It flattens an uC program into a sequence of SSA code instructions, represented as tuples of the form:
        `(operation, operands, ..., destination)`\n

        Note: This class uses the visitor pattern.
        You need to define `visit_<>` methods for each kind of AST node that you want to process, where `<>` is the node name.
    '''

    # TODO add to nodes:
    # [ ] _scope
    # [ ] _bind (?)
    # [ ] _uctype
    # see added values to class ID on 28-04 mid

    # FIXME use node.attrs['uctype'] instead of node._uctype,
    #       node.attrs['scope'] instead of node._scope, etc.
    # ref.: https://www.tutorialspoint.com/compiler_design/compiler_design_semantic_analysis.htm

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
        
    def visit_ArrayRef(self, node: ArrayRef): # [name*, subscript*]
        self.visit(node.subscript)
        if isinstance(node.subscript, ID):
            assert node.subscript._scope is not None, (
                f"`{node.subscript.name}` is not defined"
            )
        _base_type = node.subscript.type.names[-1] # i.e. int, float or char
        assert _base_type == TYPE_INT.typename, (
            f"Array indexed with non-integer type: {_base_type}"
        )
        # assert node.subscript._uctype == TYPE_INT

    def visit_Assert(self, node: Assert): # [expr*]
        self.visit(node.expr)
        assert node._uctype == TYPE_BOOL, (
            f"Expression does not evaluate to boolean: assert {node._uctype}"
        )

    def visit_Assignment(self, node: Assignment): # [op, lvalue*, rvalue*]
        self.visit(node.rvalue)
        self.visit(node.lvalue)
        if isinstance(node.lvalue, ID):
            assert node.lvalue._scope is not None, (
                f"`{node.lvalue.name}` is not defined"
            )
        # ...
    
    def visit_Break(self, node: Break): # []
        assert self.environment.cur_loop != [], (
            "Call to `break` outside of a loop"
        )
        node._bind = self.environment.cur_loop[-1]

    def visit_Constant(self, node: Constant): # [type, value]
        # see 28-04 bottommid
        pass
    
    def visit_Decl(self, node: Decl): # [name, type*, init*]
        self.visit(node.type)
        node.name._bind = node.type
        if isinstance(node.type, FuncDecl):
            assert self.environment.lookup(node.name), (
                f"`{node.name}` is not defined"
            )
    
    
    def visit_FuncCall(self, node: FuncCall): # [name*, args*]
        # see 23-04 bottomleft
        #     28-04 mid-right&left
        pass
    
    def visit_FuncDecl(self, node: FuncDecl): # [args*, type*]
        if node.args is not None:
            for arg in node.args:
                self.visit(arg)
        self.visit(node.type)
    
    def visit_FuncDef(self, node: FuncDef): # [spec*, decl*, param_decls**, body*]
        # 16-04 topright
        # 28-04 bottom left
        pass
    
    def visit_ID(self, node: ID): # [name]
        # see 28-04 bottommid
        pass
    
    def visit_If(self, node: If): # [cond*, ifthen*, ifelse*]
        pass
    
    def visit_Program(self, node: Program): # [gdecls**]
        self.environment.push(node)
        self.symtab = self.environment.peek_root()
        for gdecl in node.gdecls:
            assert isinstance(gdecl, (GlobalDecl, FuncDef))
            self.visit(gdecl)
        self.environment.pop()
    
    def visit_Read(self, node: Read): # [expr*]
        # check 23-04 middle
        pass

    def visit_Return(self, node: Return): # [expr*]
        node._uctype = TYPE_VOID
        if node.expr is not None:
            self.visit(node.expr)
            node._uctype = node.expr._uctype
        # TODO check it matches environment.cur_rtype,
        #      which should be the currently expected return type
        # 23-04 middle


    def visit_Type(self, node: Type): # [names]
        pass
    def visit_VarDecl(self, node: VarDecl): # [declname, type*]
        pass
