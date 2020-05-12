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
        self.loops = []
        self.funcs = []

    @property
    def in_loop(self): return len(self.loops) > 0 # return any(scope.kind == "loop" for scope in self.scope_stack)
    @property
    def in_func(self): return len(self.funcs) > 0 # return any(scope.kind == "func" for scope in self.scope_stack)

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
        self.visit(node.name)

        _name = node.name.attrs['name']
        assert _name in self.symtab.current_scope, f"Symbol not defined: {_name}"
        node.attrs['name'] = _name

        self.visit(node.subscript)
        if isinstance(node.subscript, ID):
            assert node.subscript.attrs['name'] in self.symtab.current_scope, \
                f"Variable {node.subscript.attrs['name']} not defined in array reference"
            _type = self.symtab.lookup(node.subscript.attrs['name'])['type']
        else:
            _type = node.subscript.attrs['type']
        assert _type == [TYPE_INT], f"Indexing with non-integer type: {_type}"

        _name_type = self.symtab.lookup(_name)['type'] if isinstance(node.name, ID) else node.name.attrs['type']
        if _name_type[0] == TYPE_ARRAY:
            node.attrs['type'] = _name_type[1:]
        elif _name_type[0] == TYPE_STRING:
            node.attrs['type'] = [TYPE_CHAR] + _name_type[1:]
        else:
            assert False, f"Type {_name_type} doesn't support array-like indexing"

    def visit_Assert(self, node: Assert): # [expr*]
        self.visit(node.expr)
        _expr_type = node.expr.attrs['type']
        assert _expr_type == [TYPE_BOOL], f"No implementation for: `assert {_expr_type}`"

    def visit_Assignment(self, node: Assignment): # [op, lvalue*, rvalue*]
        self.visit(node.lvalue)
        if isinstance(node.lvalue, ID):
            _lname = node.lvalue.name
        elif isinstance(node.lvalue, ArrayRef):
            _lname = node.lvalue.attrs['name']
            _ltype = node.lvalue.attrs['type']
        else:
            assert False, f"Assignment to invalid lvalue `{type(node.lvalue)}`"

        assert _lname in self.symtab.current_scope, f"Assignment to unknown lvalue `{_lname}`"
        
        if isinstance(node.lvalue, ID):
            _ltype = self.symtab.lookup(_lname)['type']

        self.visit(node.rvalue)
        _rname = node.rvalue.attrs.get('name', None)
        if isinstance(node.rvalue, ID):
            _rtype = self.symtab.lookup(_rname)['type']
        elif isinstance(node.rvalue, ArrayRef):
            _rtype = node.rvalue.attrs['type']
        elif isinstance(node.rvalue, FuncCall):
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

        # FIXME do operators like +=, -=, etc. need a "special treatment"?

    def visit_BinaryOp(self, node: BinaryOp): # [op, left*, right*]
        self.visit(node.left)
        self.visit(node.right)

        _operand_types = [None, None]
        for i, _operand in enumerate([node.left, node.right]):
            if isinstance(_operand, ID):
                _operand_name = _operand.name
                assert _operand_name in self.symtab.current_scope, f"Identifier `{_operand_name}` not defined"
                _type = self.symtab.lookup(_operand_name)['type']

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
        assert self.symtab.in_loop, f"Break outside a loop"

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

    def visit_Compound(self, node: Compound): # [decls**, stmts**]
        _parent = node.attrs.get('parent', None) # passed by the parent node on the AST
        if _parent is None:
            _new_scope = True # block (local) scope
            self.symtab.begin_scope()
        else:
            _new_scope = False
            # TODO
            if isinstance(_parent, FuncDef): # function scope
                # NOTE FuncDecl should also push a scope
                print("*** in function scope")
                print(f"*** parent '{_parent.attrs['name']}'",
                      self.symtab.lookup(_parent.attrs['name'])) # (debug)
            elif isinstance(_parent, While): # while-loop scope
                print("*** in while-loop scope")
            elif isinstance(_parent, For): # for-loop scope
                print("*** in for-loop scope")
            elif isinstance(_parent, If): # if-statement scope
                print("*** in if-statement scope")
            else:
                assert False, f"Unexpected type openning a compount statement: {type(_parent)}"

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
    
        if not isinstance(node.type, FuncDecl):
            assert sym_name not in self.symtab.local_scope, f"Redeclaration of `{sym_name}`"
        elif sym_name in self.symtab.local_scope:
            assert not self.symtab.lookup(sym_name).get('defined?', False), f"Redeclaration of already defined `{sym_name}`"

        sym_attrs = {}
        self.visit(node.type)
        sym_attrs['type'] = node.type.attrs['type']
        if isinstance(node.type, VarDecl):
            pass
        elif isinstance(node.type, ArrayDecl):
            sym_attrs['dim'] = node.type.attrs.get('dim', None)
        elif isinstance(node.type, FuncDecl):
            
            sym_attrs['param_types'] = node.type.attrs.get('param_types', [])
            if sym_name in self.symtab.local_scope:

                assert sym_attrs['type'] == self.symtab.lookup(sym_name)['type'], \
                    f"Redeclaration of function {sym_name} with different return type: {sym_attrs['type']} and {self.symtab.lookup(sym_name)['type']}"

                # checking parameter types
                _declared_param_types = self.symtab.lookup(sym_name)['param_types']
                assert len(sym_attrs['param_types']) == len(_declared_param_types), \
                    f"Conflicting parameter count for `{sym_name}`: {len(sym_attrs['param_types'])} passed, {len(_declared_param_types)} expected"
                for _new_type, _old_type in zip(sym_attrs['param_types'], _declared_param_types):
                    assert _new_type == _old_type, (
                        f"Conflicting types for `{sym_name}`: {_new_type} passed, {_old_type} expected"
                    )

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
        for decl in node.decls:
            self.visit(decl)

    def visit_EmptyStatement(self, node: EmptyStatement): # []
        pass

    def visit_ExprList(self, node: ExprList): # [exprs**]
        for expr in node.exprs:
            self.visit(expr)
        node.attrs['type'] = node.exprs[-1].attrs['type']

    def visit_For(self, node: For): # [init*, cond*, next*, body*]
        self.symtab.begin_scope(loop=node)

        if node.init is not None:
            self.visit(node.init)
        if node.cond is not None:
            self.visit(node.cond)
            assert node.cond.attrs['type'] == [TYPE_BOOL], f"Condition should be a bool instead of {node.cond.attrs['type']}"

        if node.next is not None:
            self.visit(node.next)

        if isinstance(node.body, Compound):
            node.body.attrs['parent'] = node
        self.visit(node.body)

        self.symtab.end_scope(loop=True)

    def visit_FuncCall(self, node: FuncCall): # [name*, args*]
        assert isinstance(node.name, ID)
        self.visit(node.name)
        _name = node.name.attrs['name']
        assert _name in self.symtab.current_scope, f"Function `{_name}` not defined"

        if node.args is not None:
            self.visit(node.args)

        _func = self.symtab.lookup(_name)
        _param_types = _func.get('param_types', [])
        _passed_args = (
            [] if node.args is None
            else node.args.exprs if isinstance(node.args, ExprList)
            else [node.args] # there's only one argument
        )
        assert len(_param_types) == len(_passed_args), (
            ("Too many" if len(_param_types) < len(_passed_args) else "Too few") +
            f" arguments in call to `{_name}`: {len(_passed_args)} passed, {len(_param_types)} expected"
        )

        for _passed_arg, _param_type in zip(_passed_args, _param_types):
            assert _passed_arg.attrs['type'] == _param_type, (
                f"Wrong argument type in call to `{_name}`: {_passed_arg.attrs['type']} passed, {_param_type} expected"
            )

        node.attrs['type'] = _func['type'][1:] # get the return type (ignoring TYPE_FUNC)
        node.attrs['name'] = _name

    def visit_FuncDecl(self, node: FuncDecl): # [args*, type*]
        self.symtab.begin_scope(func=node) # NOTE we use this so parameter names don't go to the global scope
        # FIXME I think we may actually be able use the current scope
        # and only open one for FuncDef (since it has a Compound stmt)

        assert isinstance(node.type, VarDecl)
        self.visit(node.type)
        node.attrs['type'] = [TYPE_FUNC] + node.type.attrs['type']

        if node.args is not None:
            assert isinstance(node.args, ParamList)
            self.visit(node.args)
            node.attrs['param_types'] = node.args.attrs['param_types']

        self.symtab.end_scope(func=True)

    # FIXME
    def visit_FuncDef(self, node: FuncDef): # [spec*, decl*, body*]
        sym_attrs = {}
        assert isinstance(node.spec, Type)
        self.visit(node.spec)
        node.attrs['type'] = [TYPE_FUNC] + node.spec.attrs['type']
        sym_attrs['type'] = [TYPE_FUNC] + node.spec.attrs['type'] # FIXME what's this?

        # FIXME we may need to pass param_names in FuncDecl attrs and (re-)add them to symtab here,
        # as they are popped on FuncDecl's symtab, and now we need them in the FuncDef's symtab
        assert isinstance(node.decl, Decl)
        self.visit(node.decl)
        sym = self.symtab.lookup(node.decl.name.name)
        _param_types = sym['param_types']
        sym['defined?'] = True
        # TODO add param names to symtab
        if _param_types is not None:
            pass
            # TODO assert params types (NOTE this may have to be done in Decl, as it's where FuncDecl will return to first)

        # TODO assert return type
        self.symtab.begin_scope(func=node)

        assert isinstance(node.body, Compound)
        node.attrs['name'] = node.decl.name.name # NOTE this is used for lookup on body
        node.body.attrs['parent'] = node
        self.visit(node.body)

        self.symtab.end_scope(func=True)

    def visit_GlobalDecl(self, node: GlobalDecl): # [decls**]
        for decl in node.decls:
            self.visit(decl)

    def visit_ID(self, node: ID): # [name]
        node.attrs['name'] = node.name

    def visit_If(self, node: If): # [cond*, ifthen*, ifelse*]
        self.symtab.begin_scope()

        self.visit(node.cond)
        assert node.cond.attrs['type'] == [TYPE_BOOL], f"Condition should be a bool instead of {node.cond.attrs['type']}"

        # FIXME ifthen/ifelse can be a single expression

        if isinstance(node.ifthen, Compound):
            node.ifthen.attrs['parent'] = node
        self.symtab.begin_scope()
        self.visit(node.ifthen)
        self.symtab.end_scope()

        if node.ifelse is not None:
            if isinstance(node.ifelse, Compound):
                node.ifelse.attrs['parent'] = node
            self.symtab.begin_scope()
            self.visit(node.ifelse)
            self.symtab.end_scope()

        self.symtab.end_scope()

    def visit_InitList(self, node: InitList): # [exprs**]
        self.visit(node.exprs[0])
        _type = node.exprs[0].attrs['type']
        for expr in node.exprs[1:]:
            self.visit(expr)
            assert _type == expr.attrs['type'], f"Init list must have homogeneous types: {_type} and {expr.attrs['type']}"

        if _type[0] == TYPE_CHAR:
            assert len(_type) == 1
            node.attrs['type'] = [TYPE_STRING]
        else:
            node.attrs['type'] = [TYPE_ARRAY] + _type

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
                    assert _expr.attrs['name'] in self.symtab.current_scope, (
                        f"Attempt to print unknown array: `{_expr.attrs['name']}`"
                    )
                elif isinstance(_expr, FuncCall):
                    assert _expr.attrs['name'] in self.symtab.current_scope, (
                        f"Attempt to print the return of an unknown function: `{_expr.attrs['name']}`"
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
                assert _expr.attrs['name'] in self.symtab.current_scope, (
                    f"Attempt to read into unknown array: `{_expr.attrs['name']}`"
                )
            else:
                # FIXME does it make sense to read into any other node type?
                assert False, f"Unexpected node type in read: {type(_expr)}"

    def visit_Return(self, node: Return): # [expr*]
        assert self.symtab.in_func, f"Return outside a function"

        if node.expr is not None:
            self.visit(node.expr)
            assert node.expr.attrs['type'] == self.symtab.curr_func.attrs['type'][1:], f"Returning {node.expr.attrs['type']} on a {self.symtab.curr_func.attrs['type'][1:]} function"
        else:
            assert [TYPE_VOID] == self.symtab.curr_func.attrs['type'][1:], f"Returning {[TYPE_VOID]} on a {self.symtab.curr_func.attrs['type'][1:]} function"

    def visit_Type(self, node: Type): # [names]
        node.attrs['type'] = [uC_types.from_name(name) for name in node.names]

    def visit_VarDecl(self, node: VarDecl): # [declname, type*]
        assert isinstance(node.type, Type)
        self.visit(node.type)
        node.attrs['type'] = node.type.attrs['type']

    def visit_UnaryOp(self, node: UnaryOp): # [op, expr*]
        assert node.op in uC_ops.unary_ops.values(), f"Unexpected operator in unary operation: `{node.op}`"

        self.visit(node.expr)

        _operand_name = node.expr.attrs.get('name', None)
        if isinstance(node.expr, ID):
            assert _operand_name in self.symtab.current_scope, f"Identifier `{_operand_name}` not defined"
            _type = self.symtab.lookup(_operand_name)['type']

        elif isinstance(node.expr, FuncCall):
            assert _operand_name in self.symtab.current_scope, f"Function `{_operand_name}` not defined"
            _type = self.symtab.lookup(_operand_name)['type'][1:] # ignore TYPE_FUNC

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
        self.symtab.begin_scope(loop=node)
        
        self.visit(node.cond)
        assert node.cond.attrs['type'] == [TYPE_BOOL], f"Condition should be a bool instead of {node.cond.attrs['type']}"

        if isinstance(node.body, Compound):
           node.body.attrs['parent'] = node
        self.visit(node.body)

        self.symtab.end_scope(loop=True)