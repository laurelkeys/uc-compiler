import os
import sys

from collections import ChainMap

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
        self.fname = "$global"
        self.versions = { self.fname: 0 } # version dictionary for temporaries
        self.code = [] # generated code as a list of tuples
        self.fregisters = ChainMap()
        self.fend_label = None

    @property
    def last_temp(self):
        return "%" + "%d" % (self.versions[self.fname] - 1)

    def new_temp(self, var_name=None):
        ''' Create a new temporary variable of a given scope (function name). '''
        if self.fname not in self.versions:
            self.versions[self.fname] = 0
        name = "%" + "%d" % (self.versions[self.fname])
        self.versions[self.fname] += 1
        if var_name is not None:
            self.fregisters[var_name] = name # bind the param name to the temp created
        return name

    def begin_function(self, fname):
        self.fname = fname
        self.fregisters = self.fregisters.new_child()

    def end_function(self):
        self.fname = "$global"
        self.fregisters = self.fregisters.parents

    def unwrap_type(self, _type):
        if len(_type) == 1:
            _type = _type[0]
        else:
            assert False, "!!long boy type"
        return _type

    ###########################################################
    ## SSA Code Instructions ##################################
    ###########################################################

    # Variables & Values
    def emit_alloc(self, _type, varname):
        ''' Allocate on stack (ref by register) a variable of a given type. '''
        self.code.append((f"alloc_{_type}", varname))

    def emit_global(self, _type, varname, value):
        ''' Allocate on heap a global var of a given type. value is optional. '''
        self.code.append((f"global_{_type}", varname, value))

    def emit_load(self, _type, varname, target):
        ''' Load the value of a variable (stack/heap) into target (register). '''
        self.code.append((f"load_{_type}", varname, target))

    def emit_store(self, _type, source, target):
        ''' Store the source/register into target/varname. '''
        self.code.append((f"store_{_type}", source, target))

    def emit_literal(self, _type, value, target):
        ''' Load a literal value into target. '''
        self.code.append((f"literal_{_type}", value, target))

    def emit_elem(self, _type, source, index, target):
        ''' Load into target the address of source (array) indexed by index. '''
        self.code.append((f"elem_{_type}", source, index, target))

    # Cast Operations
    def emit_fptosi(self, fvalue):
        ''' (int)fvalue == cast float to int. '''
        self.code.append(("fptosi", fvalue))

    def emit_sitofp(self, ivalue):
        ''' (float)ivalue == cast int to float. '''
        self.code.append(("sitofp", ivalue))

    # Binary & Relational/Equality/Logical Operations
    def emit_op(self, _op, _type, left, right, target):
        ''' target = left `_op` right. '''
        opcode = {
            '+':  'add', '-':  'sub',
            '*':  'mul', '/':  'div', '%': 'mod',

            '&&': 'and', '||': 'or',

            '==': 'eq',  '!=': 'ne',
            '<':  'lt',  '<=': 'le',
            '>':  'gt',  '>=': 'ge',
        }
        self.code.append((f"{opcode[_op]}_{_type}", left, right, target))

    # Labels & Branches
    def emit_label(self, label):
        ''' Label definition. '''
        # NOTE we also use this to emit the
        #      end of a function definition
        self.code.append((label, ))

    def emit_jump(self, target):
        ''' Jump to a target label. '''
        self.code.append(("jump", target))

    def emit_cbranch(self, expr_test, true_target, false_target):
        ''' Conditional branch. '''
        self.code.append(("cbranch", expr_test, true_target, false_target))

    # Functions & Built-ins
    def emit_define(self, source):
        ''' Function definition. `source` is a function label . '''
        self.code.append(("define", source))

    def emit_call(self, source, opt_target=None):
        ''' Call a function. `target` is an optional return value. '''
        self.code.append(
           ("call", source, ) if opt_target is None else
           ("call", source, opt_target)
        )

    def emit_return(self, _type, opt_target=None):
        ''' Return from function. `target` is an optional return value. '''
        self.code.append(
            (f"return_{_type}", ) if opt_target is None else
            (f"return_{_type}", opt_target)
        )

    def emit_param(self, _type, source):
        ''' `source` is an actual parameter. '''
        self.code.append((f"param_{_type}", source))

    def emit_read(self, _type, source):
        ''' Read value to `source`. '''
        self.code.append((f"read_{_type}", source))

    def emit_print(self, _type, source):
        ''' Print value of `source`. '''
        self.code.append((f"print_{_type}", source))

    ###########################################################
    ## Code Generation for AST Nodes ##########################
    ###########################################################

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
        self.visit(node.left)
        self.visit(node.right)

        _target = self.new_temp()

        self.emit_op(
            _op=node.op,
            _type=self.unwrap_type(node.left.attrs['type']),
            left=node.left.attrs['reg'],
            right=node.right.attrs['reg'],
            target=_target
        )

        node.attrs['reg'] = _target

    def visit_Break(self, node: Break): # []
        print(node.__class__.__name__, node.attrs)
        # TODO bind its 'parent' function, so we can call jump
        pass
    def visit_Cast(self, node: Cast): # [type*, expr*]
        print(node.__class__.__name__, node.attrs)
        pass

    def visit_Compound(self, node: Compound): # [decls**, stmts**]
        print(node.__class__.__name__, node.attrs)
        if node.decls is not None:
            for decl in node.decls:
                self.visit(decl)
        if node.stmts is not None:
            for stmt in node.stmts:
                self.visit(stmt)

    def visit_Constant(self, node: Constant): # [type, value]
        print(node.__class__.__name__, node.attrs)
        _target = self.new_temp()
        _type = self.unwrap_type(node.attrs['type'])
        self.code.append(
            (f"literal_{_type}", node.value, _target)
        )
        node.attrs['reg'] = _target#node.value
        pass

    def visit_Decl(self, node: Decl): # [name*, type*, init*]
        print(node.__class__.__name__, node.attrs)
        # FIXME triple-check we're visiting init where necessary
        _type = node.attrs['type']
        _name = node.attrs['name']
        if _type[0] == TYPE_FUNC:
            node.type.attrs['name'] = _name
            self.visit(node.type)
        else: # variable declaration
            _type = self.unwrap_type(_type)
            #self.visit(node.name) #@remove
            if node.attrs.get('global?', False):
                self.fregisters[_name] =  f"@{_name}"
                if node.init is None:
                    inst = (f"global_{_type}", f"@{_name}", )
                else:
                    self.visit(node.init)
                    inst = (f"global_{_type}", f"@{_name}", node.init.attrs['reg'])
                node.attrs['reg'] = f"@{_name}"
                self.code.append(inst)
            else:
                _target = self.new_temp()
                self.fregisters[_name] = _target
                self.code.append((f"alloc_{_type}", _target))
                if node.init is not None:
                    self.visit(node.init)
                    self.code.append(
                        # (f"store_{_type}", self.last_temp, _target)
                        (f"store_{_type}", node.init.attrs['reg'], _target)
                    )
                node.attrs['reg'] = f"@{_name}"

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
        if node.attrs.get('defined?', False):
            # "reserve" registers for args, return value and an end label
            node.attrs['args_reg'] = (
                [] if node.args is None
                else [self.new_temp() for _ in node.args]
            )
            node.attrs['ret_reg'] = self.new_temp('$return')
            # FIXME moving the 'end_label' here might be better #@remove

            # alloc a variable for each arg
            if node.args is not None:
                for _arg, _arg_reg in zip(node.args, node.attrs['args_reg']):
                    _actual_reg = self.new_temp(_arg.name.name)
                    _type = self.unwrap_type(_arg.attrs['type'])
                    self.code.append(
                        (f"alloc_{_type}", _actual_reg)
                    )
                    self.code.append(
                        (f"store_{_type}", _arg_reg, _actual_reg)
                    )

            self.new_temp('$end_label')

    def visit_FuncDef(self, node: FuncDef): # [spec*, decl*, body*]
        print(node.__class__.__name__, node.attrs)
        self.begin_function(node.attrs['name'])

        self.code.append(("define", f"@{self.fname}"))

        node.decl.type.attrs['defined?'] = True
        self.visit(node.decl)

        self.visit(node.body)

        self.code.append((self.fregisters['$end_label'][1:], ))

        _type = self.unwrap_type(node.attrs['type'][1:]) # ignore TYPE_FUNC
        if _type == TYPE_VOID:
            self.code.append((f"return_{_type}", ))
        else:
            _target = self.new_temp()
            self.code.extend([
                (f"load_{_type}", self.fregisters['$return'], _target),
                (f"return_{_type}", _target),
            ])

        self.end_function()

    def visit_GlobalDecl(self, node: GlobalDecl): # [decls**]
        print(node.__class__.__name__, node.attrs)
        for decl in node.decls:
            decl.attrs['global?'] = True
            self.visit(decl)

    def visit_ID(self, node: ID): # [name]
        print(node.__class__.__name__, node.attrs)

        # FIXME move this code to Decl as it has both name and type in attrs

        # FIXME we might want to add 'parent' before calling
        # this, so we can check it's 'reg', idk (?)
        if self.fname == "$global":
            print("REMOVEME") #@remove this if
            node.attrs['reg'] = f"@{node.name}"
            self.fregisters[node.name] =  f"@{node.name}"
        else:
            _type = self.unwrap_type(node.attrs['type'])
            _target = self.new_temp()
            print("======== QUERIED", self.fregisters)
            self.code.append(
                (f"load_{_type}", self.fregisters[node.name], _target)
            )
            node.attrs['reg'] = _target

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
        if node.expr is not None:
            self.visit(node.expr)
            # _source = self.last_temp # return value of node.expr
            _source = node.expr.attrs['reg'] # return value of node.expr
            _ftype = self.unwrap_type(node.expr.attrs['type'])
            self.code.append(
                (f"store_{_ftype}", _source, self.fregisters['$return'])
            )
        self.code.append(
            ("jump", self.fregisters['$end_label'])
        )

    def visit_Type(self, node: Type): # [names]
        print(node.__class__.__name__, node.attrs)
        pass
    def visit_VarDecl(self, node: VarDecl): # [declname, type*]
        print(node.__class__.__name__, node.attrs)
        self.visit(node.type)
        pass

    def visit_UnaryOp(self, node: UnaryOp): # [op, expr*]
        print(node.__class__.__name__, node.attrs)
        # _unop_target = self.new_temp()

        self.visit(node.expr)
        _expr_reg = node.expr.attrs['reg']
        _expr_type = self.unwrap_type(node.expr.attrs['type'])

        if node.op == '+':
            pass
        elif node.op == '-':
            _zero_reg = self.new_temp()
            _unop_target = self.new_temp()
            self.code.extend([
                (f"literal_{_expr_type}", _expr_type.default, _zero_reg),
                (f"sub_{_expr_type}", _zero_reg, _expr_reg, _unop_target)
            ])
        elif node.op[-2:] == '++':
            if node.op[0] == 'p':
                pass
            else:
                pass
        elif node.op[-2:] == '--':
            if node.op[0] == 'p':
                pass
            else:
                pass
        elif node.op == '&':
            pass
        elif node.op == '*':
            pass
        elif node.op == '!':
            pass
        else:
            assert False, f"Unexpected unary operator on code generation: `{node.op}`"

        node.attrs['reg'] = _unop_target

    def visit_While(self, node: While): # [cond*, body*]
        print(node.__class__.__name__, node.attrs)
        pass
