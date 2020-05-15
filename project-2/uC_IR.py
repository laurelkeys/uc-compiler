import os
import sys
from collections import defaultdict

import uC_ops
import uC_types

from uC_AST import *
from uC_types import (TYPE_INT, TYPE_FLOAT, TYPE_CHAR, TYPE_STRING, TYPE_VOID,
                      TYPE_ARRAY, TYPE_BOOL, TYPE_FUNC)

###########################################################
## uC Intermediate Representation (IR) ####################
###########################################################

class GenerateCode(NodeVisitor):
    ''' Node visitor class that creates 3-address encoded instruction sequences. '''

    def __init__(self):
        super(GenerateCode, self).__init__()
        self.fname = "main"
        self.versions = { self.fname: 0 } # version dictionary for temporaries
        self.code = [] # generated code as a list of tuples

    def new_temp(self):
        ''' Create a new temporary variable of a given scope (function name). '''
        if self.fname not in self.versions:
            self.versions[self.fname] = 0
        name = "%" + "%d" % (self.versions[self.fname])
        self.versions[self.fname] += 1
        return name

    def visit_ArrayDecl(self, node: ArrayDecl): # [type*, dim*]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_ArrayRef(self, node: ArrayRef): # [name*, subscript*]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_Assert(self, node: Assert): # [expr*]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_Assignment(self, node: Assignment): # [op, lvalue*, rvalue*]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_BinaryOp(self, node: BinaryOp): # [op, left*, right*]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_Break(self, node: Break): # []
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_Cast(self, node: Cast): # [type*, expr*]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_Compound(self, node: Compound): # [decls**, stmts**]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_Constant(self, node: Constant): # [type, value]
        print(node.__class__.__name__, node.attrs)
        node.attrs['loc'] = node.value
        pass

    def visit_Decl(self, node: Decl): # [name, type*, init*]
        print(node.__class__.__name__, node.attrs)
        if node.init is not None:
            self.visit(node.init)
        _type = node.attrs['type']
        _name = node.attrs['name']
        if len(_type) == 1:
            _type = _type[0]
            if node.attrs.get('global?', False):
                if node.init is None:
                    inst = (f"global_{_type}", f"@{_name}", )
                else:
                    inst = (f"global_{_type}", f"@{_name}", node.init.attrs['loc'])
                node.attrs['loc'] = f"@{_name}"
            else:
                assert False, "1"
        else:
            assert False, "2"
        self.code.append(inst)

    def visit_DeclList(self, node: DeclList): # [decls**]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_EmptyStatement(self, node: EmptyStatement): # []
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_ExprList(self, node: ExprList): # [exprs**]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_For(self, node: For): # [init*, cond*, next*, body*]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_FuncCall(self, node: FuncCall): # [name*, args*]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_FuncDecl(self, node: FuncDecl): # [args*, type*]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_FuncDef(self, node: FuncDef): # [spec*, decl*, body*]
        print(node.__class__.__name__, node.attrs)
        pass

    def visit_GlobalDecl(self, node: GlobalDecl): # [decls**]
        print(node.__class__.__name__, node.attrs)
        for decl in node.decls:
            decl.attrs['global?'] = True
            self.visit(decl)

    def visit_ID(self, node: ID): # [name]
        print(node.__class__.__name__, node.attrs)
        node.attrs['loc'] = f"@{node.name}" # TODO maybe move @ to Global
        pass

    def visit_If(self, node: If): # [cond*, ifthen*, ifelse*]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_InitList(self, node: InitList): # [exprs**]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_ParamList(self, node: ParamList): # [params**]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_Print(self, node: Print): # [expr*]
        print(node.__class__.__name__, node.attrs)
        pass

    def visit_Program(self, node: Program): # [gdecls**]
        print(node.__class__.__name__, node.attrs)
        for gdecl in node.gdecls:
            self.visit(gdecl)

    def visit_PtrDecl(self, node: PtrDecl): # [type*]
        print(node.__class__.__name__, node.attrs)
        raise NotImplementedError

    def visit_Read(self, node: Read): # [expr*]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_Return(self, node: Return): # [expr*]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_Type(self, node: Type): # [names]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_VarDecl(self, node: VarDecl): # [declname, type*]
        print(node.__class__.__name__, node.attrs)
        self.visit(node.type)
        pass
    def visit_UnaryOp(self, node: UnaryOp): # [op, expr*]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_While(self, node: While): # [cond*, body*]
        print(node.__class__.__name__, node.attrs)
        pass
