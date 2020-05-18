import os
import sys

from collections import ChainMap

from uC_AST import *

###########################################################
## uC Intermediate Representation (IR) ####################
###########################################################


class GenerateCode(NodeVisitor):
    """ Node visitor class that creates 3-address encoded instruction sequences. """

    def __init__(self):
        super(GenerateCode, self).__init__()
        self.fname = "$global"
        self.versions = {self.fname: 0}  # version dictionary for temporaries
        self.code = []  # generated code as a list of tuples
        self.fregisters = ChainMap()  # map of registers
        self.farray_dim = ChainMap()  # map of array dims

    def new_temp(self, var_name=None):
        """ Create a new temporary variable of a given scope (function name). """
        if self.fname not in self.versions:
            self.versions[self.fname] = 0
        name = "%" + "%d" % (self.versions[self.fname])
        self.versions[self.fname] += 1
        if var_name is not None:
            self.fregisters[var_name] = name  # bind the param name to the temp created
        return name

    def begin_function(self, fname):
        self.fname = fname
        self.fregisters = self.fregisters.new_child()
        self.farray_dim = self.farray_dim.new_child()

    def end_function(self):
        self.fname = "$global"
        self.fregisters = self.fregisters.parents
        self.farray_dim = self.farray_dim.parents

    # @remove NOTE sometimes we're returning a UCType, and at others we are
    # returning a string, we should choose one way and fix the tests we do
    def unwrap_type(self, _type, _dim=None):
        if len(_type) == 1:
            return _type[0]
        elif _type[0] == TYPE_ARRAY:
            assert _dim is not None, f"!!mising dim for type: {_type}"
            # FIXME (incomplete) fix this for multi dimensional arrays
            _base_type = _type[-1]

            product = 1
            type_tail = ""
            for d in reversed(_dim):
                product *= d
                type_tail = f"_{product}{type_tail}"
            return str(_base_type) + type_tail
        else:
            assert False, f"!!fix this type: {_type}"

    ###########################################################
    ## SSA Code Instructions ##################################
    ###########################################################

    # Variables & Values
    def emit_alloc(self, _type, varname):
        """ Allocate on stack (ref by register) a variable of a given type. """
        self.code.append((f"alloc_{_type}", varname))

    def emit_global(self, _type, varname, opt_value=None):
        """ Allocate on heap a global var of a given type. value is optional. """
        self.code.append(
            (f"global_{_type}", varname,)
            if opt_value is None
            else (f"global_{_type}", varname, opt_value)
        )

    def emit_load(self, _type, varname, target):
        """ Load the value of a variable (stack/heap) into target (register). """
        self.code.append((f"load_{_type}", varname, target))

    def emit_store(self, _type, source, target):
        """ Store the source/register into target/varname. """
        self.code.append((f"store_{_type}", source, target))

    def emit_literal(self, _type, value, target):
        """ Load a literal value into target. """
        self.code.append((f"literal_{_type}", value, target))

    def emit_elem(self, _type, source, index, target):
        """ Load into target the address of source (array) indexed by index. """
        self.code.append((f"elem_{_type}", source, index, target))

    # Cast Operations
    def emit_fptosi(self, fvalue, target):
        """ (int)fvalue == cast float to int. """
        self.code.append(("fptosi", fvalue, target))

    def emit_sitofp(self, ivalue, target):
        """ (float)ivalue == cast int to float. """
        self.code.append(("sitofp", ivalue, target))

    # Binary & Relational/Equality/Logical Operations
    def emit_op(self, _op, _type, left, right, target):
        """ target = left `_op` right. """
        opcode = {
            "+": "add",
            "-": "sub",
            "*": "mul",
            "/": "div",
            "%": "mod",
            "&&": "and",
            "||": "or",
            "==": "eq",
            "!=": "ne",
            "<": "lt",
            "<=": "le",
            ">": "gt",
            ">=": "ge",
        }
        self.code.append((f"{opcode[_op]}_{_type}", left, right, target))

    # Labels & Branches
    def emit_label(self, label):
        """ Label definition. """
        # NOTE we also use this to emit the
        #      end of a function definition
        self.code.append((label,))

    def emit_jump(self, target):
        """ Jump to a target label. """
        self.code.append(("jump", target))

    def emit_cbranch(self, expr_test, true_target, false_target):
        """ Conditional branch. """
        self.code.append(("cbranch", expr_test, true_target, false_target))

    # Functions & Built-ins
    def emit_define(self, source):
        """ Function definition. `source` is a function label . """
        self.code.append(("define", source))

    def emit_call(self, source, opt_target=None):
        """ Call a function. `target` is an optional return value. """
        self.code.append(
            ("call", source,) if opt_target is None else ("call", source, opt_target)
        )

    def emit_return(self, _type, opt_target=None):
        """ Return from function. `target` is an optional return value. """
        self.code.append(
            (f"return_{_type}",) if opt_target is None else (f"return_{_type}", opt_target)
        )

    def emit_param(self, _type, source):
        """ `source` is an actual parameter. """
        self.code.append((f"param_{_type}", source))

    def emit_read(self, _type, source):
        """ Read value to `source`. """
        self.code.append((f"read_{_type}", source))

    def emit_print(self, _type, source=None):
        """ Print value of `source`. """
        self.code.append((f"print_{_type}",) if source is None else (f"print_{_type}", source))

    def create_assert_message(self, coord):
        message = f"assertion_fail on {coord.line}:{coord.column}"
        var_name = f"@assert_message_{coord.line}_{coord.column}"
        self.code.insert(
            0, ("global_string", var_name, message)
        )  # add to the beginning of the code
        return var_name

    def create_array_initlist(self, _type, coord, array):
        var_name = f"@array_{coord.line}_{coord.column}"
        self.code.insert(
            0, (f"global_{_type}", var_name, array)
        )  # add to the beginning of the code
        return var_name

    def create_string(self, coord, string):
        var_name = f"@str_{coord.line}_{coord.column}"
        self.code.insert(
            0, (f"global_string", var_name, string)
        )  # add to the beginning of the code
        return var_name

    ###########################################################
    ## Code Generation for AST Nodes ##########################
    ###########################################################

    def visit_ArrayDecl(self, node: ArrayDecl):  # [type*, dim*]
        pass

    def visit_ArrayRef(self, node: ArrayRef):  # [name*, subscript*]
        if isinstance(node.name, ArrayRef):
            node.name.attrs["child?"] = True
            self.visit(node.name)

        self.visit(node.subscript)  # emits load

        if node.attrs.get("child?", False):
            _dim = self.farray_dim[node.attrs["name"]]
            _type = self.unwrap_type(node.attrs["type"], _dim)
            # NOTE ugly hack
            _prod = int(_type.split("_")[-node.attrs["type"].count(TYPE_ARRAY)])
            _prod_target = self.new_temp()
            self.emit_literal(TYPE_INT, value=_prod, target=_prod_target)
            _target = self.new_temp()
            self.emit_op(
                "*",
                TYPE_INT,
                left=_prod_target,
                right=node.subscript.attrs["reg"],
                target=_target,
            )
            # NOTE necessary for arrays with more than 2 dimensions
            if isinstance(node.name, ArrayRef):
                _fixed_subs = self.new_temp()  # multiply dimensions in matrices
                self.emit_op(
                    "+",
                    TYPE_INT,
                    left=node.name.attrs["reg"],  # FIXME think: may be name
                    right=_target,
                    target=_fixed_subs,
                )
                _target = _fixed_subs
        else:
            _subs_reg = node.subscript.attrs["reg"]
            if isinstance(node.name, ArrayRef):
                _fixed_subs = self.new_temp()  # multiply dimensions in matrices
                self.emit_op(
                    "+",
                    TYPE_INT,
                    left=node.name.attrs["reg"],  # FIXME think: may be name
                    right=node.subscript.attrs["reg"],
                    target=_fixed_subs,
                )
                _subs_reg = _fixed_subs

            _elem_target = self.new_temp()
            self.emit_elem(
                _type=self.unwrap_type(node.attrs["type"]),
                source=self.fregisters[node.attrs["name"]],
                index=_subs_reg,
                target=_elem_target,
            )
            if node.attrs.get("load_ptr?", False):
                _target = self.new_temp()
                self.emit_load(
                    _type=str(self.unwrap_type(node.attrs["type"])) + "_*",
                    varname=_elem_target,
                    target=_target,
                )
            else:
                _target = _elem_target

        node.attrs["reg"] = _target

    def visit_Assert(self, node: Assert):  # [expr*]
        self.visit(node.expr)

        _true_target = self.new_temp()
        _false_target = self.new_temp()
        _end_target = self.new_temp()

        self.emit_cbranch(node.expr.attrs["reg"], _true_target, _false_target)
        self.emit_label(_true_target[1:])
        self.emit_jump(_end_target)

        self.emit_label(_false_target[1:])
        assert_message = self.create_assert_message(node.coord)
        self.emit_print("string", assert_message)
        self.emit_jump(self.fregisters["$end_label"])

        self.emit_label(_end_target[1:])

    def visit_Assignment(self, node: Assignment):  # [op, lvalue*, rvalue*]
        if not isinstance(node.lvalue, ID):
            self.visit(node.lvalue)

        node.rvalue.attrs["load_ptr?"] = True
        self.visit(node.rvalue)

        if isinstance(node.lvalue, ArrayRef):
            _ltype = str(self.unwrap_type(node.lvalue.attrs["type"])) + "_*"
            _target = node.lvalue.attrs["reg"]
        else:
            _ltype = self.unwrap_type(node.lvalue.attrs["type"])
            _target = self.fregisters[node.lvalue.attrs["name"]]

        _source = node.rvalue.attrs["reg"]

        if len(node.op) > 1:  # +=, -=, /=, *=
            _op = node.op[0]
            _temp_target = self.new_temp()
            self.emit_op(_op, _ltype, left=_target, right=_source, target=_temp_target)
            _source = _temp_target

        self.emit_store(_type=_ltype, source=_source, target=_target)

        node.attrs["reg"] = _target

    def visit_BinaryOp(self, node: BinaryOp):  # [op, left*, right*]
        node.left.attrs["load_ptr?"] = True
        node.right.attrs["load_ptr?"] = True
        self.visit(node.left)
        self.visit(node.right)

        _target = self.new_temp()
        self.emit_op(
            _op=node.op,
            _type=self.unwrap_type(node.left.attrs["type"]),
            left=node.left.attrs["reg"],
            right=node.right.attrs["reg"],
            target=_target,
        )
        node.attrs["reg"] = _target

    def visit_Break(self, node: Break):  # []
        self.emit_jump(self.fregisters["$break"])

    def visit_Cast(self, node: Cast):  # [type*, expr*]
        node.expr.attrs["load_ptr?"] = True
        self.visit(node.expr)

        _target = self.new_temp()
        if node.attrs["type"] == TYPE_FLOAT:
            self.emit_sitofp(node.expr.attrs["reg"], _target)
        else:
            self.emit_fptosi(node.expr.attrs["reg"], _target)
        node.attrs["reg"] = _target

    def visit_Compound(self, node: Compound):  # [decls**, stmts**]
        if node.decls is not None:
            for decl in node.decls:
                self.visit(decl)
        if node.stmts is not None:
            for stmt in node.stmts:
                self.visit(stmt)

    def visit_Constant(self, node: Constant):  # [type, value]
        if self.fname == "$global":
            # FIXME retest this (added the `if` for init lists)
            node.attrs["reg"] = node.value
        else:
            _target = self.new_temp()
            _type = self.unwrap_type(node.attrs["type"])
            self.emit_literal(_type, value=node.value, target=_target)
            node.attrs["reg"] = _target

    def visit_Decl(self, node: Decl):  # [name*, type*, init*]
        # FIXME triple-check we're visiting init where necessary
        _type = node.attrs["type"]
        _name = node.attrs["name"]

        if _type[0] == TYPE_FUNC:
            node.type.attrs["name"] = _name
            self.visit(node.type)

        else:  # variable declaration
            if _type[0] == TYPE_ARRAY:
                _type = self.unwrap_type(_type, node.attrs["dim"])
                self.farray_dim[node.attrs["name"]] = node.attrs["dim"]
            elif _type[0] == TYPE_STRING:
                assert len(_type) == 1
                _type = self.unwrap_type([TYPE_ARRAY, TYPE_CHAR], node.attrs["dim"])
                self.farray_dim[node.attrs["name"]] = node.attrs["dim"]
            else:
                _type = self.unwrap_type(_type)

            if node.attrs.get("global?", False):
                self.fregisters[_name] = f"@{_name}"
                if node.init is not None:
                    node.init.attrs["load_ptr?"] = True
                    self.visit(node.init)
                self.emit_global(
                    _type,
                    varname=f"@{_name}",
                    opt_value=None if node.init is None else node.init.attrs["reg"],
                )
                node.attrs["reg"] = f"@{_name}"

            else:
                _target = self.new_temp()
                self.fregisters[_name] = _target
                self.emit_alloc(_type, varname=_target)
                if node.init is not None:
                    if isinstance(node.init, Constant) and node.init.attrs["type"] == [
                        TYPE_STRING
                    ]:
                        node.init.attrs["reg"] = self.create_string(
                            coord=node.coord, string=node.init.attrs["value"]
                        )
                    else:
                        node.init.attrs["load_ptr?"] = True
                        self.visit(node.init)
                    self.emit_store(_type, source=node.init.attrs["reg"], target=_target)
                node.attrs[
                    "reg"
                ] = f"@{_name}"  # FIXME shouldn't this be _target? (need to test..)

    def visit_DeclList(self, node: DeclList):  # [decls**]
        if node.decls is not None:
            for decl in node.decls:
                self.visit(decl)

    def visit_EmptyStatement(self, node: EmptyStatement):  # []
        pass

    def visit_ExprList(self, node: ExprList):  # [exprs**]
        for expr in node.exprs:
            self.visit(expr)
        node.attrs["reg"] = node.exprs[-1].attrs["reg"]

    def visit_For(self, node: For):  # [init*, cond*, next*, body*]

        if node.init is not None:
            node.init.attrs["load_ptr?"] = True
            self.visit(node.init)

        loop_top = self.new_temp()
        self.emit_label(loop_top[1:])

        loop_body = self.new_temp()
        loop_end = self.new_temp()

        self.fregisters["$break"] = loop_end
        if node.cond is not None:
            self.visit(node.cond)
            self.emit_cbranch(
                expr_test=node.cond.attrs["reg"], true_target=loop_body, false_target=loop_end,
            )

        self.emit_label(loop_body[1:])
        self.visit(node.body)

        if node.next is not None:
            node.next.attrs["load_ptr?"] = True
            self.visit(node.next)

        self.emit_jump(loop_top)
        self.emit_label(loop_end[1:])

    def visit_FuncCall(self, node: FuncCall):  # [name*, args*]
        _passed_args = (
            []
            if node.args is None
            else node.args.exprs
            if isinstance(node.args, ExprList)
            else [node.args]  # there's only one argument
        )

        for _arg in _passed_args:
            _arg.attrs["load_ptr?"] = True
            self.visit(_arg)  # emits load
        for _arg in _passed_args:
            self.emit_param(_type=self.unwrap_type(_arg.attrs["type"]), source=_arg.attrs["reg"])

        _target = self.new_temp()
        self.emit_call(source=f"@{node.attrs['name']}", opt_target=_target)

        node.attrs["reg"] = _target

    def visit_FuncDecl(self, node: FuncDecl):  # [args*, type*]
        if node.attrs.get("defined?", False):
            # reserve registers for args and the return value
            node.attrs["args_reg"] = []
            if node.args is not None:
                node.attrs["args_reg"].extend([self.new_temp() for _ in node.args])
            node.attrs["ret_reg"] = self.new_temp("$return")

            # alloc a variable for each argument
            if node.args is not None:
                for _arg, _arg_reg in zip(node.args, node.attrs["args_reg"]):
                    _type = self.unwrap_type(_arg.attrs["type"])
                    _actual_reg = self.new_temp(_arg.name.name)
                    self.emit_alloc(_type, varname=_actual_reg)
                    self.emit_store(_type, source=_arg_reg, target=_actual_reg)

            self.new_temp("$end_label")  # reserve and end label

    def visit_FuncDef(self, node: FuncDef):  # [spec*, decl*, body*]
        self.begin_function(node.attrs["name"])
        self.emit_define(source=f"@{self.fname}")
        node.decl.type.attrs["defined?"] = True

        self.visit(node.decl)
        self.visit(node.body)

        self.emit_label(label=self.fregisters["$end_label"][1:])  # ignore the %

        _type = self.unwrap_type(node.attrs["type"][1:])  # ignore TYPE_FUNC
        if _type == TYPE_VOID:
            self.emit_return(_type)
        else:
            _target = self.new_temp()
            self.emit_load(_type, varname=self.fregisters["$return"], target=_target)
            self.emit_return(_type, opt_target=_target)

        self.end_function()

    def visit_GlobalDecl(self, node: GlobalDecl):  # [decls**]
        for decl in node.decls:
            decl.attrs["global?"] = True
            self.visit(decl)

    def visit_ID(self, node: ID):  # [name]
        _target = self.new_temp()
        self.emit_load(
            _type=self.unwrap_type(node.attrs["type"]),
            varname=self.fregisters[node.name],
            target=_target,
        )
        node.attrs["reg"] = _target

    def visit_If(self, node: If):  # [cond*, ifthen*, ifelse*]
        _then = self.new_temp()
        _else = self.new_temp()
        if node.ifelse is None:
            _end = _else
        else:
            _end = self.new_temp()

        self.visit(node.cond)
        self.emit_cbranch(
            expr_test=node.cond.attrs["reg"], true_target=_then, false_target=_else,
        )

        self.emit_label(_then[1:])
        if node.ifthen is not None:  # NOTE this should always exist
            self.visit(node.ifthen)

        if node.ifelse is not None:
            self.emit_jump(_end)
            self.emit_label(_else[1:])
            self.visit(node.ifelse)

        self.emit_label(_end[1:])

    def visit_InitList(self, node: InitList):  # [exprs**]
        _fname = self.fname
        self.fname = "$global"

        _target = []
        for expr in node.exprs:
            expr.attrs["child?"] = True
            self.visit(expr)
            _target.append(expr.attrs["reg"])

        if node.attrs.get("child?", False):
            node.attrs["reg"] = _target
        else:
            node.attrs["reg"] = self.create_array_initlist(
                _type=self.unwrap_type(node.attrs["type"], node.attrs["dim"]),
                coord=node.coord,
                array=_target,
            )

        self.fname = _fname

    def visit_ParamList(self, node: ParamList):  # [params**]
        pass

    def visit_Print(self, node: Print):  # [expr*]
        if node.expr is None:
            self.emit_print(TYPE_VOID)
        else:
            _print_exprs = node.expr.exprs if isinstance(node.expr, ExprList) else [node.expr]
            for expr in _print_exprs:
                _type = expr.attrs["type"]
                if _type == [TYPE_STRING]:
                    source = self.create_string(coord=expr.coord, string=expr.attrs["value"])
                else:
                    expr.attrs["load_ptr?"] = True
                    self.visit(expr)
                    source = expr.attrs["reg"]
                self.emit_print(_type=self.unwrap_type(_type), source=source)

    def visit_Program(self, node: Program):  # [gdecls**]
        for gdecl in node.gdecls:
            self.visit(gdecl)

    def visit_PtrDecl(self, node: PtrDecl):  # [type*]
        raise NotImplementedError

    def visit_Read(self, node: Read):  # [expr*]
        if node.expr is not None:
            _read_exprs = node.expr.exprs if isinstance(node.expr, ExprList) else [node.expr]
            for expr in _read_exprs:
                # NOTE expr is either an ID or an ArrayRef
                _type = self.unwrap_type(expr.attrs["type"])
                _read_reg = self.new_temp()
                self.emit_read(_type, source=_read_reg)

                if isinstance(node.expr, ID):
                    _expr_reg = self.fregisters[expr.attrs["name"]]
                else:  # ArrayRef
                    _type = str(_type) + "_*"
                    self.visit(expr)
                    _expr_reg = expr.attrs["reg"]

                self.emit_store(_type, source=_read_reg, target=_expr_reg)

    def visit_Return(self, node: Return):  # [expr*]
        if node.expr is not None:
            self.visit(node.expr)
            self.emit_store(
                _type=self.unwrap_type(node.expr.attrs["type"]),
                source=node.expr.attrs["reg"],  # return value of node.expr
                target=self.fregisters["$return"],
            )
        self.emit_jump(target=self.fregisters["$end_label"])

    def visit_Type(self, node: Type):  # [names]
        pass

    def visit_VarDecl(self, node: VarDecl):  # [declname, type*]
        self.visit(node.type)
        pass

    def visit_UnaryOp(self, node: UnaryOp):  # [op, expr*]
        node.expr.attrs["load_ptr?"] = True
        self.visit(node.expr)  # if ID emits load
        _expr_reg = node.expr.attrs["reg"]
        _expr_type = self.unwrap_type(node.expr.attrs["type"])

        if node.op == "+":
            _unop_target = _expr_reg  # pass

        elif node.op == "-":
            _zero_reg = self.new_temp()
            _unop_target = self.new_temp()
            self.emit_literal(_expr_type, value=0, target=_zero_reg)
            self.emit_op(
                _op="-", _type=_expr_type, left=_zero_reg, right=_expr_reg, target=_unop_target
            )

        elif node.op[-2:] == "++":
            _one_reg = self.new_temp()
            _unop_target = self.new_temp()
            self.emit_literal(_expr_type, value=1, target=_one_reg)
            self.emit_op(
                _op="+",
                _type=_expr_type,
                left=node.expr.attrs["reg"],
                right=_one_reg,
                target=_unop_target,
            )
            assert isinstance(node.expr, (ID, ArrayRef))
            self.emit_store(  # update value
                _type=_expr_type,
                source=_unop_target,
                target=self.fregisters[node.expr.name]  # FIXME changed target from _expr_reg,
                # but still have to test for ArrayRef
            )
            if node.op[0] == "p":  # NOTE suffix/postfix increment
                _unop_target = node.expr.attrs["reg"]

        elif node.op[-2:] == "--":
            _one_reg = self.new_temp()
            _unop_target = self.new_temp()
            self.emit_literal(_expr_type, value=1, target=_one_reg)
            self.emit_op(
                _op="-",
                _type=_expr_type,
                left=node.expr.attrs["reg"],
                right=_one_reg,
                target=_unop_target,
            )
            assert isinstance(node.expr, (ID, ArrayRef))
            self.emit_store(  # update value
                _type=_expr_type,
                source=_unop_target,
                target=self.fregisters[node.expr.name],  # FIXME see above ++
            )
            if node.op[0] == "p":  # NOTE suffix/postfix decrement
                _unop_target = node.expr.attrs["reg"]

        elif node.op == "&":
            raise NotImplementedError
        elif node.op == "*":
            raise NotImplementedError

        elif node.op == "!":
            _unop_target = self.new_temp()
            self.code.append(("not_bool", _expr_reg, _unop_target))

        else:
            assert False, f"Unexpected unary operator on code generation: `{node.op}`"

        node.attrs["reg"] = _unop_target

    def visit_While(self, node: While):  # [cond*, body*]

        loop_top = self.new_temp()
        self.emit_label(loop_top[1:])

        loop_body = self.new_temp()
        loop_end = self.new_temp()

        self.fregisters["$break"] = loop_end
        if node.cond is not None:
            self.visit(node.cond)
            self.emit_cbranch(
                expr_test=node.cond.attrs["reg"], true_target=loop_body, false_target=loop_end,
            )

        self.emit_label(loop_body[1:])

        self.visit(node.body)
        self.emit_jump(loop_top)
        self.emit_label(loop_end[1:])
