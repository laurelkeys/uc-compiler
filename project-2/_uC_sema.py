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
        print(len(self.symbol_table.maps), "> push") # FIXME debug only
        self.symbol_table = self.symbol_table.new_child()
        if loop is not None: self.loops.append(loop)
        if func is not None: self.funcs.append(func)

    def end_scope(self, loop: bool = False, func: bool = False):
        ''' Pop the current scope's symbol table, effectively deleting it.\n
            If `loop`/`func` is `True`, the `curr_loop`/`curr_func` is also popped.
        '''
        print(len(self.symbol_table.maps) - 1, "> pop", self.local_scope) # FIXME debug only
        self.symbol_table = self.symbol_table.parents
        if loop: self.loops.pop()
        if func: self.funcs.pop()

    @property
    def current_scope(self): return self.symbol_table # contains everything that's currently visible
    @property
    def global_scope(self): return self.symbol_table.maps[-2] # NOTE [-1] has the built-in functions
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
        assert isinstance(node.type, (VarDecl, ArrayDecl))
        self.visit(node.type)
        if node.type.attrs['type'][0] == TYPE_CHAR:
            assert len(node.type.attrs['type']) == 1
            node.attrs['type'] = [TYPE_STRING] # represents a [TYPE_ARRAY, TYPE_CHAR]
        else:
            node.attrs['type'] = [TYPE_ARRAY] + node.type.attrs['type']

        if node.dim is not None:
            self.visit(node.dim)
            if isinstance(node.dim, Constant):
                node.attrs['dim'] = node.dim.value # FIXME
                _dim_type = node.dim.attrs['type']
            elif isinstance(node.dim, ID):
                node.attrs['dim'] = node.dim.name # FIXME
                # NOTE we may only have this value at run-time
                assert node.dim.name in self.symtab.current_scope, (
                    f"Undeclared identifier in array dimension: `{node.dim.name}`"
                )
                _dim_type = self.symtab.lookup(node.dim.name)['type']
            else:
                _dim_type = node.dim.attrs['type']
            assert _dim_type == [TYPE_INT], (
                f"Size of array has non-integer type {_dim_type}"
            )

    def visit_ArrayRef(self, node: ArrayRef): # [name*, subscript*]
        # TODO assert subscript is of type int
        pass

    def visit_Assert(self, node: Assert): # [expr*]
        self.visit(node.expr)
        _expr_type = node.expr.attrs['type']
        assert _expr_type == [TYPE_BOOL], f"No implementation for: `assert {_expr_type}`"

    def visit_Assignment(self, node: Assignment): # [op, lvalue*, rvalue*]
        self.visit(node.lvalue)
        if isinstance(node.lvalue, ID):
            _lname = node.lvalue.name
            _ltype = self.symtab.lookup(_lname)['type']
        elif isinstance(node.lvalue, ArrayRef):
            _lname = node.lvalue.name.name
            _ltype = self.symtab.lookup(_lname)['type']
            # NOTE we're interested in the indexed type
            if len(_ltype) == 1:
                assert _ltype[0] == TYPE_STRING
                _ltype = [TYPE_CHAR]
            else:
                assert _ltype[0] == TYPE_ARRAY
                _ltype = _ltype[1:]
        else:
            assert False, f"Assignment to invalid lvalue `{type(node.lvalue)}`"

        assert _lname in self.symtab.current_scope, f"Assignment to unknown lvalue `{_lname}`"

        self.visit(node.rvalue)
        _rname = None
        if isinstance(node.rvalue, ID):
            _rname = node.rvalue.name
            _rtype = self.symtab.lookup(_rname)['type']
        elif isinstance(node.rvalue, ArrayRef):
            _rname = node.rvalue.name.name
            _rtype = self.symtab.lookup(_rname)['type']
            # NOTE we're interested in the indexed type
            if len(_rtype) == 1:
                assert _rtype[0] == TYPE_STRING
                _rtype = [TYPE_CHAR]
            else:
                assert _rtype[0] == TYPE_ARRAY
                _rtype = _rtype[1:]
        elif isinstance(node.rvalue, FuncCall):
            _rname = node.rvalue.name.name
            _rtype = self.symtab.lookup(_rname)['type'][1:] # ignore TYPE_FUNC
        else:
            _rtype = node.rvalue.attrs['type']

        if _rname is not None:
            assert _rname in self.symtab.current_scope, (
                f"Assignment of unknown rvalue: `{_lname}` = `{_rname}`"
            )

        assert _ltype == _rtype, f"Type mismatch: `{_ltype} {node.op} {_rtype}`"

        assert node.op in uC_ops.assign_ops.values(), f"Unexpected operator in adssignment operation: `{node.op}`"

        assert node.op in _ltype[0].assign_ops, ( # use the "outermost" type
            f"Operation not supported by type {_ltype}: `{_ltype} {node.op} {_rtype}`"
        )

        node.attrs['type'] = _ltype

        # FIXME do operators like +=, -=, etc. need a "special treatment"? (probably)

    def visit_BinaryOp(self, node: BinaryOp): # [op, left*, right*]
        self.visit(node.left)
        self.visit(node.right)

        _operand_types = [None, None]
        for i, _operand in enumerate([node.left, node.right]):
            if isinstance(_operand, ID):
                _operand_name = _operand.name
                assert _operand_name in self.symtab.current_scope, f"Identifier `{_operand_name}` not defined"
                _type = self.symtab.lookup(_operand_name)['type']

            elif isinstance(_operand, FuncCall):
                _operand_name = _operand.name.name
                assert _operand_name in self.symtab.current_scope, f"Function `{_operand_name}` not defined"
                _type = self.symtab.lookup(_operand_name)['type'][1:] # ignore TYPE_FUNC

            else:
                _type = _operand.attrs['type']

            assert TYPE_FUNC not in _type
            _operand_types[i] = _type
        _ltype, _rtype = _operand_types

        assert _ltype == _rtype, f"Type mismatch: `{_ltype} {node.op} {_rtype}`"

        if node.op in uC_ops.binary_ops.values():
            _type_ops = _ltype[0].binary_ops # use the "outermost" type
            node.attrs['type'] = _ltype

        elif node.op in uC_ops.rel_ops.values():
            _type_ops = _ltype[0].rel_ops # use the "outermost" type
            node.attrs['type'] = [TYPE_BOOL]

        else:
            assert False, f"Unexpected operator in binary operation: `{node.op}`"

        assert node.op in _type_ops, f"Operation not supported by type {_ltype}: `{_ltype} {node.op} {_rtype}`"

    def visit_Break(self, node: Break): # []
        # TODO assert we are in a "func" scope
        pass

    def visit_Cast(self, node: Cast): # [type*, expr*]
        assert isinstance(node.type, Type)
        self.visit(node.type)
        _dst_type = node.type.attrs['type']

        self.visit(node.expr)
        _src_type = node.expr.attrs['type']

        _valid_cast = False
        if (_src_type == _dst_type or
            _src_type == [TYPE_INT] and _dst_type == [TYPE_FLOAT] or
            _src_type == [TYPE_FLOAT] and _dst_type == [TYPE_INT]):
            _valid_cast = True

        assert _valid_cast, f"Cast from `{_src_type}` to `{_dst_type}` is not supported"
        node.attrs['type'] = _dst_type

    def visit_Compound(self, node: Compound, parent: Node = None): # [decls**, stmts**]
        if parent is None:
            _new_scope = True # block (local) scope
            self.symtab.begin_scope()
        else:
            _new_scope = False
            # TODO
            if isinstance(parent, FuncDef): # function scope
                # NOTE FuncDecl should also push a scope
                pass
            elif isinstance(parent, While): # while-loop scope
                pass
            elif isinstance(parent, For): # for-loop scope
                pass
            elif isinstance(parent, If): # if-statement scope
                pass
            else:
                assert False, f"Unexpected type openning a compount statement: {type(parent)}"

        if node.decls is not None:
            for decl in node.decls:
                self.visit(decl)
        if node.stmts is not None:
            for stmt in node.stmts:
                self.visit(stmt)

        if _new_scope:
            self.symtab.end_scope()

    def visit_Constant(self, node: Constant): # [type, value]
        node.attrs['type'] = [uC_types.from_name(node.type)]

    def visit_Decl(self, node: Decl): # [name, type*, init*]
        assert isinstance(node.name, ID)
        self.visit(node.name)
        sym_name = node.name.name
        assert sym_name not in self.symtab.local_scope, f"Redeclaration of `{sym_name}`"

        sym_attrs = {}
        self.visit(node.type)
        sym_attrs['type'] = node.type.attrs['type']
        if isinstance(node.type, VarDecl):
            pass
        elif isinstance(node.type, ArrayDecl):
            sym_attrs['dim'] = node.type.attrs.get('dim', None)
        elif isinstance(node.type, FuncDecl):
            sym_attrs['param_types'] = node.type.attrs.get('param_types', None)
        else:
            assert False, f"Unexpected type {type(node.type)} for node.type"

        if node.init is not None:
            self.visit(node.init)
            print(f"%%%% type(node.init) == {type(node.init)}") # FIXME remove
            assert node.init.attrs['type'] == sym_attrs['type'], (
                f"Implicit conversions are not supported: {sym_attrs['type']} = {node.init.attrs['type']}"
            )
            # NOTE here's where we'd treat ArrayDecl with init and check that dim is Constant

        self.symtab.add(
            name=sym_name,
            attributes=sym_attrs # TODO add scope
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
        self.symtab.begin_scope()
        # FIXME I think we may actually be able use the current scope
        # and only open one for FuncDef (since it has a Compound stmt)

        assert isinstance(node.type, VarDecl)
        self.visit(node.type)
        node.attrs['type'] = [TYPE_FUNC] + node.type.attrs['type']

        if node.args is not None:
            assert isinstance(node.args, ParamList)
            self.visit(node.args)
            node.attrs['param_types'] = node.args.attrs['param_types']

        self.symtab.end_scope()

    # FIXME
    def visit_FuncDef(self, node: FuncDef): # [spec*, decl*, body*]
        self.symtab.begin_scope()

        sym_attrs = {}
        assert isinstance(node.spec, Type)
        self.visit(node.spec)
        sym_attrs['type'] = [TYPE_FUNC] + node.spec.attrs['type']

        assert isinstance(node.decl, Decl)
        self.visit(node.decl)
        _param_types = self.symtab.lookup(node.decl.name.name)['param_types']
        if _param_types is not None:
            pass
            # TODO assert params types

        # TODO assert type

        assert isinstance(node.body, Compound)
        self.visit(node.body)

        self.symtab.end_scope()

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
            # FIXME a type(param) == Decl, which means it's added
            # to the current scope.. a special check in visit_Decl
            # may be needed to avoid this (and simply use .attrs)
            assert isinstance(param, Decl)
            _param_type = self.symtab.lookup(param.name.name)['type']
            param_types.append(_param_type)
        node.attrs['param_types'] = param_types

    def visit_Print(self, node: Print): # [expr*]
        if node.expr is not None:
            self.visit(node.expr)
            _print_exprs = node.expr.exprs if isinstance(node.expr, ExprList) else [node.expr]
            for _expr in _print_exprs:
                if isinstance(_expr, ID):
                    assert _expr.name in self.symtab.current_scope, (
                        f"Attempt to print unknown identifier: `{_expr.name}`"
                    )
                elif isinstance(_expr, ArrayRef):
                    assert _expr.name.name in self.symtab.current_scope, (
                        f"Attempt to print unknown array: `{_expr.name.name}`"
                    )
                elif isinstance(_expr, FuncCall):
                    assert _expr.name.name in self.symtab.current_scope, (
                        f"Attempt to print the return of an unknown function: `{_expr.name.name}`"
                    )
                else:
                    pass # FIXME I think it's okay to print pretty much anything (binops, unops, functions, etc.)

    def visit_Program(self, node: Program): # [gdecls**]
        self.symtab.begin_scope()

        for gdecl in node.gdecls:
            assert isinstance(gdecl, (GlobalDecl, FuncDef))
            self.visit(gdecl)

        self.symtab.end_scope()

    def visit_PtrDecl(self, node: PtrDecl): # [type*]
        raise NotImplementedError

    def visit_Read(self, node: Read): # [expr*]
        self.visit(node.expr)
        _read_exprs = node.expr.exprs if isinstance(node.expr, ExprList) else [node.expr]
        for _expr in _read_exprs:
            if isinstance(_expr, ID):
                assert _expr.name in self.symtab.current_scope, (
                    f"Attempt to read into unknown identifier: `{_expr.name}`"
                )
            elif isinstance(_expr, ArrayRef):
                assert _expr.name.name in self.symtab.current_scope, (
                    f"Attempt to read into unknown array: `{_expr.name.name}`"
                )
            else:
                # FIXME does it make sense to read into any other node type?
                assert False, f"Unexpected node type in read: {type(_expr)}"


    def visit_Return(self, node: Return): # [expr*]
        # TODO assert we are in a "func" scope
        pass

    def visit_Type(self, node: Type): # [names]
        node.attrs['type'] = [uC_types.from_name(name) for name in node.names]

    def visit_VarDecl(self, node: VarDecl): # [declname, type*]
        assert isinstance(node.type, Type)
        self.visit(node.type)
        node.attrs['type'] = node.type.attrs['type']

    def visit_UnaryOp(self, node: UnaryOp): # [op, expr*]
        assert node.op in uC_ops.unary_ops.values(), f"Unexpected operator in unary operation: `{node.op}`"

        self.visit(node.expr)

        if isinstance(node.expr, ID):
            _operand_name = node.expr.name
            assert _operand_name in self.symtab.current_scope, f"Identifier `{_operand_name}` not defined"
            _type = self.symtab.lookup(_operand_name)['type']

        elif isinstance(node.expr, FuncCall):
            _operand_name = node.expr.name.name
            assert _operand_name in self.symtab.current_scope, f"Function `{_operand_name}` not defined"
            _type = self.symtab.lookup(_operand_name)['type'][1:] # ignore TYPE_FUNC

        # FIXME special check for ArrayRef

        else:
            _type = node.expr.attrs['type']

        assert TYPE_FUNC not in _type

        assert node.op in _type[0].unary_ops, ( # use the "outermost" type
            f"Operation not supported by type {_type}: " + (
                f"`{node.op}{_type}`" if node.op[0] != 'p' else f"`{_type}{node.op[1:]}`"
            )
        )

        node.attrs['type'] = _type

    def visit_While(self, node: While): # [cond*, body*]
        pass