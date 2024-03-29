from typing import Dict, List

import llvmlite.ir as ir

from uC_AST import *
from uC_types import *

###########################################################
## uC to LLVM IR ##########################################
###########################################################

class LLVMCodeGenerator(NodeVisitor):
    ''' Node visitor class that creates LLVM IR code. '''

    def __init__(self) -> None:
        super(LLVMCodeGenerator, self).__init__()

        # Top-level container of all other LLVM IR objects
        self.module: ir.Module = ir.Module()

        # Current function's IR builder
        self.builder: ir.IRBuilder = None

        # Global and current function symbol tables
        self.func_symtab: Dict[str, ir.AllocaInstr] = {}
        self.global_symtab: Dict[str, ir.AllocaInstr] = {}

        # Save the current function's "exit" block and "retval" address
        self.func_exit_block = None
        self.func_return_addr = None

        # Break point stack
        self.loop_end_blocks = []

    def generate_code(self, node: Node) -> str:
        assert isinstance(node, Program)
        self.visit(node)
        return str(self.module)

    def __addr(self, var_name: str) -> ir.AllocaInstr:
        ''' Return the address pointed by `var_name`. '''
        return self.func_symtab.get(var_name) or self.global_symtab[var_name]

    def __elem_addr(self, array_addr, index_value):
        ''' WIP wrapper for `getelementptr`. '''
        # FIXME
        # https://llvm.org/docs/GetElementPtr.html#summary
        return self.builder.gep(
            name="elem.addr",
            ptr=array_addr,
            inbounds=True,
            indices=[
                ir.Constant(typ=ir.IntType(64), constant=0),
                index_value
            ]
        )

    def __alloca(self, var_name: str, ir_type: ir.Type) -> ir.AllocaInstr:
        ''' Create an alloca instruction in the entry of the current function,
            and update `func_symtab[var_name]` with the allocated stack address.
        '''
        assert self.builder is not None
        assert isinstance(var_name, str) and isinstance(ir_type, ir.Type)

        size = None  # FIXME add as arg for implementing arrays/strings

        with self.builder.goto_entry_block():
            var_addr = self.builder.alloca(typ=ir_type, size=size, name=f"{var_name}.addr")
            assert var_name not in self.func_symtab  # NOTE sanity check
            self.func_symtab[var_name] = var_addr

        return var_addr

    def __global_var(
        self, var_name: str, ir_type: ir.Type, init_value: ir.Value = None, is_const: bool = False
    ) -> ir.GlobalVariable:
        ''' Create a global variable and update `global_symtab[var_name]` with it. '''
        assert isinstance(var_name, str) and isinstance(ir_type, ir.Type)

        global_var = ir.GlobalVariable(self.module, typ=ir_type, name=var_name)
        assert var_name not in self.global_symtab  # NOTE sanity check
        self.global_symtab[var_name] = global_var

        if is_const:
            global_var.linkage = "internal"  # https://llvm.org/docs/LangRef.html#linkage
            global_var.global_constant = True

        if init_value is not None:
            global_var.initializer = init_value

        return global_var

    def __global_const(self, var_name: str, init_value: ir.Value) -> ir.GlobalVariable:
        ''' Wrapper for `__global_var(var_name, init_value.type, init_value, True)`. '''
        return self.__global_var(
            self.module.get_unique_name(var_name),
            ir_type=init_value.type,
            init_value=init_value,
            is_const=True
        )

    def __terminate(self, target: ir.Block):
        ''' Terminates the current basic block (if it wasn't already). '''
        curr_block = self.builder.block
        if not curr_block.is_terminated:
            self.builder.branch(target=target)

    def __binop(self, binop: str, lhs: ir.Value, rhs: ir.Value) -> ir.Value:
        ''' Return the equivalent of `lhs <binop> rhs`, abstracting type-handling. '''
        if isinstance(lhs.type, ir.IntType):
            if binop in TYPE_INT.binary_ops:
                return {
                    '+': lambda: self.builder.add(lhs, rhs, name="i.add"),
                    '-': lambda: self.builder.sub(lhs, rhs, name="i.sub"),
                    '*': lambda: self.builder.mul(lhs, rhs, name="i.mul"),
                    '/': lambda: self.builder.sdiv(lhs, rhs, name="i.div"),
                    '%': lambda: self.builder.srem(lhs, rhs, name="i.rem"),
                }[binop]()

            elif binop in TYPE_INT.rel_ops:
                return self.builder.icmp_signed(binop, lhs, rhs, name="i.cmp")

            elif binop in TYPE_BOOL.binary_ops:
                assert lhs.type.width == rhs.type.width == 1
                return {
                    '&&': lambda: self.builder.and_(lhs, rhs, name="b.and"),
                    '||': lambda: self.builder.or_(lhs, rhs, name="b.or"),
                }[binop]()

            else:
                assert False, binop

        elif isinstance(lhs.type, ir.DoubleType):
            if binop in TYPE_FLOAT.binary_ops:
                return {
                    '+': lambda: self.builder.fadd(lhs, rhs, name="f.add"),
                    '-': lambda: self.builder.fsub(lhs, rhs, name="f.sub"),
                    '*': lambda: self.builder.fmul(lhs, rhs, name="f.mul"),
                    '/': lambda: self.builder.fdiv(lhs, rhs, name="f.div"),
                    '%': lambda: self.builder.frem(lhs, rhs, name="f.rem"),
                }[binop]()

            elif binop in TYPE_FLOAT.rel_ops:
                return self.builder.fcmp_ordered(binop, lhs, rhs, name="f.cmp")

            else:
                assert False, binop

        else:
            assert False, type(lhs)  # TODO implement

    def __unop(self, unop: str, expr_value: ir.Value, expr_addr: ir.AllocaInstr = None) -> ir.Value:
        ''' Return the equivalent of `<unop> operand`, or `operand <unop>`, abstracting type-handling.

            Note: `expr_addr` is used (and required) for operations that change the operand (e.g. ++, --).
        '''
        if isinstance(expr_value.type, ir.IntType):
            assert unop in TYPE_INT.unary_ops, unop

            if unop == '+':
                return expr_value

            elif unop == '-':
                return self.builder.sub(lhs=UCLLVM.Const.i0, rhs=expr_value, name="i.neg")

            elif unop.endswith('++'):
                inc_expr_value = self.builder.add(lhs=expr_value, rhs=UCLLVM.Const.i1, name="i.inc")
                self.builder.store(value=inc_expr_value, ptr=expr_addr)
                return inc_expr_value

            elif unop.endswith('--'):
                dec_expr_value = self.builder.sub(lhs=expr_value, rhs=UCLLVM.Const.i1, name="i.dec")
                self.builder.store(value=dec_expr_value, ptr=expr_addr)
                return dec_expr_value

            else:
                assert False, unop  # FIXME implement

        elif isinstance(expr_value.type, ir.DoubleType):
            assert unop in TYPE_INT.unary_ops, unop

            if unop == '+':
                return expr_value

            elif unop == '-':
                return self.builder.fsub(lhs=UCLLVM.Const.f0, rhs=expr_value, name="f.neg")

            elif unop.endswith('++'):
                inc_expr_value = self.builder.fadd(lhs=expr_value, rhs=UCLLVM.Const.f1, name="f.inc")
                self.builder.store(value=inc_expr_value, ptr=expr_addr)
                return inc_expr_value

            elif unop.endswith('--'):
                dec_expr_value = self.builder.fsub(lhs=expr_value, rhs=UCLLVM.Const.f1, name="f.dec")
                self.builder.store(value=dec_expr_value, ptr=expr_addr)
                return dec_expr_value

            else:
                assert False, unop  # FIXME implement

        else:
            assert False, type(expr_value)  # TODO implement

    def __bytearray(self, string: str, encode: bool = True) -> ir.Constant:
        ''' Make a byte array constant from `string`.

            Note: if `encode is True` the string is null terminated and ASCII encoded.
        '''
        if encode: string = (string + '\00').encode('ascii')

        string_bytes = bytearray(string)

        return ir.Constant(
            typ=ir.ArrayType(element=ir.IntType(8), count=len(string_bytes)),
            constant=string_bytes
        )

    def __printf(self, fmt: str, fmt_name: str = None, *fmt_args):
        ''' Emit a call to C's printf, e.g.: `printf(fmt, *fmt_args)`.  '''
        assert isinstance(fmt, str)

        global_fmt = self.__global_const(fmt_name or "printf.fmt", self.__bytearray(fmt))
        ptr_fmt = self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())
        try:
            printf_fn = self.module.globals["printf"]
        except KeyError:
            printf_fn = ir.Function(
                self.module,
                name="printf",
                ftype=ir.FunctionType(
                    return_type=ir.IntType(32),
                    args=[ir.IntType(8).as_pointer()],
                    var_arg=True
                )
            )

        return self.builder.call(printf_fn, args=[ptr_fmt] + list(fmt_args), name="printf.call")

    def __scanf(self, fmt: str, fmt_name: str = None, *fmt_args):
        ''' Emit a call to C's scanf, e.g.: `scanf(fmt, *fmt_args)`.  '''
        assert isinstance(fmt, str)

        global_fmt = self.__global_const(fmt_name or "scanf.fmt", self.__bytearray(fmt))
        ptr_fmt = self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())
        try:
            scanf_fn = self.module.globals["scanf"]
        except KeyError:
            scanf_fn = ir.Function(
                self.module,
                name="scanf",
                ftype=ir.FunctionType(
                    return_type=ir.IntType(32),
                    args=[ir.IntType(8).as_pointer()],
                    var_arg=True
                )
            )

        return self.builder.call(scanf_fn, args=[ptr_fmt] + list(fmt_args), name="scanf.call")

    def visit_ArrayDecl(self, node: ArrayDecl): pass  # NOTE handled in Decl

    def visit_ArrayRef(self, node: ArrayRef):
        if isinstance(node.name, ID):
            index_value = self.visit(node.subscript)
            array_addr = self.__addr(node.name.name)
            elem_addr = self.__elem_addr(array_addr, index_value)

        else:
            dummy, reversed_index_values = node, []
            while isinstance(dummy, ArrayRef):
                reversed_index_values.append(self.visit(dummy.subscript))
                dummy = dummy.name

            assert isinstance(dummy, ID)
            array_addr = self.__addr(dummy.name)

            elem_addr = array_addr
            for index_value in reversed_index_values[::-1]:
                elem_addr = self.__elem_addr(elem_addr, index_value)

        return self.builder.load(ptr=elem_addr, name="elem")

    def visit_Assert(self, node: Assert):
        expr_value = self.visit(node.expr)

        true_bb = ir.Block(self.builder.function, "assert.true")
        false_bb = ir.Block(self.builder.function, "assert.false")
        self.builder.cbranch(cond=expr_value, truebr=true_bb, falsebr=false_bb)

        # False:
        self.builder.function.basic_blocks.append(false_bb)
        self.builder.position_at_start(block=false_bb)

        self.__printf(f"Assertion failed {node.coord}", "assert.msg")
        self.builder.branch(target=self.func_exit_block)

        # True:
        self.builder.function.basic_blocks.append(true_bb)
        self.builder.position_at_start(true_bb)

    def visit_Assignment(self, node: Assignment):

        if isinstance(node.lvalue, ID):
            lhs_addr = self.__addr(node.lvalue.name)
        elif isinstance(node.lvalue, ArrayRef):
            # FIXME generating unnecessary code
            if isinstance(node.lvalue.name, ID):
                lhs_addr = self.__elem_addr(
                    array_addr=self.__addr(node.lvalue.name.name),
                    index_value=self.visit(node.lvalue.subscript)
                )
            else:
                dummy, reversed_index_values = node.lvalue, []
                while isinstance(dummy, ArrayRef):
                    reversed_index_values.append(self.visit(dummy.subscript))
                    dummy = dummy.name

                assert isinstance(dummy, ID)
                array_addr = self.__addr(dummy.name)

                elem_addr = array_addr
                for index_value in reversed_index_values[::-1]:
                    elem_addr = self.__elem_addr(elem_addr, index_value)

                lhs_addr = elem_addr
        else:
            assert False, node.lvalue  # TODO implement

        rhs_value = self.visit(node.rvalue)

        if node.op != "=":
            assert len(node.op) == 2, node.op
            lhs_value = self.builder.load(ptr=lhs_addr, name=node.lvalue.name)
            rhs_value = self.__binop(node.op[0], lhs_value, rhs_value)

        self.builder.store(value=rhs_value, ptr=lhs_addr)
        return rhs_value

    def visit_BinaryOp(self, node: BinaryOp):

        lhs_value = self.visit(node.left)
        rhs_value = self.visit(node.right)

        return self.__binop(node.op, lhs_value, rhs_value)

    def visit_Break(self, node: Break):
        assert len(self.loop_end_blocks) > 0
        self.builder.branch(target=self.loop_end_blocks[-1])

    def visit_Cast(self, node: Cast):
        assert len(node.type.names) == 1, node.type.names

        expr_value = self.visit(node.expr)
        assert isinstance(expr_value.type, (ir.IntType, ir.DoubleType))

        if node.type.names[0] == TYPE_INT.typename:
            return expr_value if isinstance(expr_value, ir.IntType) else (
                self.builder.fptosi(expr_value, typ=UCLLVM.Type.Int)
            )

        if node.type.names[0] == TYPE_FLOAT.typename:
            return expr_value if isinstance(expr_value, ir.DoubleType) else (
                self.builder.sitofp(expr_value, typ=UCLLVM.Type.Float)
            )

        assert False

    def visit_Compound(self, node: Compound):
        for decl in node.decls or []:
            self.visit(decl)
        for stmt in node.stmts or []:
            self.visit(stmt)

    def visit_Constant(self, node: Constant):

        if node.type == TYPE_CHAR.typename:
            unquoted_char = node.value[1:-1]
            return ir.Constant(typ=UCLLVM.Type.Char, constant=ord(unquoted_char))

        if node.type == TYPE_STRING.typename:
            unquoted_str = node.value[1:-1]
            return self.__bytearray(unquoted_str)

        return ir.Constant(typ=UCLLVM.Type.of([node.type]), constant=node.value)

    def visit_Decl(self, node: Decl):

        name = node.name.name

        if isinstance(node.type, FuncDecl):
            funcdecl: FuncDecl = node.type

            # Create an ir.Function to represent funcdecl
            fn_args = []
            for arg_decl in funcdecl.args or []:
                arg_vardecl = arg_decl.type
                fn_args.append(UCLLVM.Type.of(arg_vardecl.type.names))

            fn_type = ir.FunctionType(
                return_type=UCLLVM.Type.of(funcdecl.type.type.names),
                args=fn_args
            )

            fn_name = name
            fn = self.module.globals.get(fn_name)
            if fn is None:
                # Create a new function and name its arguments
                fn = ir.Function(module=self.module, ftype=fn_type, name=fn_name)
                for arg, arg_decl in zip(fn.args, funcdecl.args or []):
                    arg.name = arg_decl.name.name
            else:
                # Assert that all we've seen is the function's prototype
                assert isinstance(fn, ir.Function), f"Function/global name collision '{fn_name}'"
                assert fn.is_declaration, f"Redefinition of '{fn_name}'"
                assert len(fn.function_type.args) == len(fn_type.args), (
                    f"Definition of '{fn_name}' with wrong argument count"
                )

            return fn

        elif isinstance(node.type, VarDecl):
            vardecl: VarDecl = node.type

            var_name = name
            var_type = UCLLVM.Type.of(vardecl.type.names)

            if node.init is None:
                init_value = UCLLVM.Const.zero(var_type)
            else:
                init_value = self.visit(node.init)

            # Allocate space for the variable and store its optional initial value
            if self.builder is not None:
                # NOTE we're inside a function
                var_addr = self.__alloca(var_name, var_type)
                self.builder.store(value=init_value, ptr=var_addr)
            else:
                # NOTE we assume this is a GlobalDecl
                var_addr = self.__global_var(var_name, var_type)
                var_addr.initializer = init_value

            return init_value

        elif isinstance(node.type, ArrayDecl):
            arraydecl: ArrayDecl = node.type

            array_name = name
            array_dims = []

            # Get the base element type of the array
            base_type = arraydecl
            while isinstance(base_type, ArrayDecl):
                if base_type.dim is None:
                    array_dims.append(base_type.dim)
                else:
                    assert isinstance(base_type.dim, Constant)
                    array_dims.append(base_type.dim.value)
                base_type = base_type.type

            assert isinstance(base_type, VarDecl)
            assert isinstance(base_type.type, Type)
            elem_type = UCLLVM.Type.of(base_type.type.names)

            # Create the optional initialization list
            if node.init is None:
                array_values = None  # NOTE zeroinitializer
            else:
                if isinstance(node.init, InitList):
                    def _array_values(init):
                        return (
                            [self.visit(expr) for expr in init.exprs]
                            if not isinstance(init.exprs[0], InitList)
                            else [_array_values(expr) for expr in init.exprs]
                        )

                    def _array_dims(values):
                        return (
                            []
                            if not isinstance(values, list)
                            else [len(values)] + _array_dims(values[0])
                        )

                    array_values = _array_values(node.init)
                    array_dims = _array_dims(array_values)  # NOTE updates possibly None values

                elif isinstance(node.init, Constant):
                    assert elem_type == UCLLVM.Type.Char
                    assert node.init.type == TYPE_STRING.typename

                    # FIXME check if it's a string at the start,
                    #       then simply call self.visit(node.init),
                    #       as _array_value is already what we need

                    _array_value = self.visit(node.init)
                    array_values = _array_value.constant
                    array_dims = [_array_value.type.count]

                else:
                    assert False

            # Allocate space for the array
            array_type = elem_type
            for dim in array_dims[::-1]:
                array_type = ir.ArrayType(element=array_type, count=dim)

            array_value = ir.Constant(typ=array_type, constant=array_values)

            if self.builder is not None:
                # NOTE we're inside a function
                array_addr = self.__alloca(array_name, array_type)
                if node.init is not None:
                    self.builder.store(value=array_value, ptr=array_addr)  # FIXME might need wrapping
            else:
                # NOTE we assume this is a GlobalDecl
                array_addr = self.__global_var(array_name, array_type)
                if node.init is not None:
                    array_addr.initializer = array_value

            return array_value

        elif isinstance(node.type, PtrDecl):
            raise NotImplementedError

    def visit_DeclList(self, node: DeclList):
        for decl in node.decls:
            self.visit(decl)

    def visit_EmptyStatement(self, node: EmptyStatement): pass

    def visit_ExprList(self, node: ExprList): pass  # NOTE handled in FuncCall

    def visit_For(self, node: For):
        # Start insertion onto the current block
        self.builder.position_at_end(block=self.builder.block)

        # Create basic blocks in the current function to express the control flow
        cond_bb = ir.Block(self.builder.function, "for.cond")
        body_bb = ir.Block(self.builder.function, "for.body")
        end_bb = ir.Block(self.builder.function, "for.end")

        self.loop_end_blocks.append(end_bb)

        # Init:
        if node.init is not None:
            self.visit(node.init)

        # Condition:
        self.builder.branch(target=cond_bb)

        self.builder.function.basic_blocks.append(cond_bb)
        self.builder.position_at_start(block=cond_bb)

        if node.cond is None:
            self.builder.branch(target=body_bb)
        else:
            cond_value = self.visit(node.cond)
            self.builder.cbranch(cond=cond_value, truebr=body_bb, falsebr=end_bb)

        # Body:
        self.builder.function.basic_blocks.append(body_bb)
        self.builder.position_at_start(block=body_bb)

        self.visit(node.body)
        if node.next is not None:
            self.visit(node.next)

        self.__terminate(target=cond_bb)

        # End:
        self.builder.function.basic_blocks.append(end_bb)
        self.builder.position_at_start(block=end_bb)
        self.loop_end_blocks.pop()

    def visit_FuncCall(self, node: FuncCall):

        fn_name = node.name.name
        fn = self.module.globals.get(fn_name)

        args = []
        if isinstance(node.args, ExprList):
            for arg in node.args or []:
                arg_addr = self.visit(arg)
                args.append(arg_addr)
        else:
            arg_addr = self.visit(node.args)
            args.append(arg_addr)

        return self.builder.call(fn, args=args, name=f"{fn_name}.call")

    def visit_FuncDecl(self, node: FuncDecl): pass  # NOTE handled in Decl

    def visit_FuncDef(self, node: FuncDef):

        # Reset the current function symbol table
        self.func_symtab = {}

        # Generate an ir.Function from the prototype (i.e. the function declaration)
        fn: ir.Function = self.visit(node.decl)

        # Create a new basic block to start insertion into
        func_entry_block = fn.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block=func_entry_block)

        if fn.ftype.return_type is not UCLLVM.Type.Void:
            self.func_return_addr = self.__alloca(var_name="retval", ir_type=fn.ftype.return_type)
            self.builder.store(value=UCLLVM.Const.zero(fn.ftype.return_type), ptr=self.func_return_addr)

        # Add the function arguments to the stack (and the symbol table)
        for arg in fn.args:
            arg_addr = self.__alloca(var_name=arg.name, ir_type=arg.type)
            self.builder.store(value=arg, ptr=arg_addr)

        self.func_exit_block = ir.Block(self.builder.function, "exit")

        # Finish off generating the function
        self.visit(node.body)

        # Return
        self.__terminate(target=self.func_exit_block)

        self.builder.function.basic_blocks.append(self.func_exit_block)
        self.builder.position_at_start(block=self.func_exit_block)

        if self.func_return_addr is not None:
            ret_value = self.builder.load(self.func_return_addr, "retval")
            self.builder.ret(ret_value)
        else:
            self.builder.ret_void()

        self.func_exit_block = None
        self.func_return_addr = None
        self.builder = None
        return fn

    def visit_GlobalDecl(self, node: GlobalDecl):
        for decl in node.decls:
            self.visit(decl)

    def visit_ID(self, node: ID):
        var_addr = self.__addr(node.name)
        return self.builder.load(ptr=var_addr, name=node.name)

    def visit_If(self, node: If):
        # Start insertion onto the current block
        self.builder.position_at_end(block=self.builder.block)

        # Create basic blocks in the current function to express the control flow
        then_bb = ir.Block(self.builder.function, "if.then")
        if node.ifelse is not None:
            else_bb = ir.Block(self.builder.function, "if.else")
        end_bb = ir.Block(self.builder.function, "if.end")

        # Condition:
        cond_value = self.visit(node.cond)

        self.builder.cbranch(
            cond=cond_value,
            truebr=then_bb,
            falsebr=end_bb if node.ifelse is None else else_bb
        )

        # Then:
        self.builder.function.basic_blocks.append(then_bb)
        self.builder.position_at_start(block=then_bb)

        self.visit(node.ifthen)
        self.__terminate(target=end_bb)

        # Else:
        if node.ifelse is not None:
            self.builder.function.basic_blocks.append(else_bb)
            self.builder.position_at_start(block=else_bb)

            self.visit(node.ifelse)
            self.__terminate(target=end_bb)

        # End:
        self.builder.function.basic_blocks.append(end_bb)
        self.builder.position_at_start(block=end_bb)

    def visit_InitList(self, node: InitList): raise NotImplementedError

    def visit_ParamList(self, node: ParamList): pass  # NOTE handled in Decl (for FuncDecl)

    def visit_Print(self, node: Print):
        _fmt_dict = {
            TYPE_INT.typename:    r"%d",
            TYPE_FLOAT.typename:  r"%f",
            TYPE_CHAR.typename:   r"%c",
            TYPE_STRING.typename: r"%s",
            TYPE_BOOL.typename:   r"%d",
        }

        if node.expr is None:
            self.__printf("\n", "print.eol")

        elif isinstance(node.expr, Constant):
            _value = self.visit(node.expr)
            _addr = self.__global_const("print.arg", _value)
            _fmt = _fmt_dict[node.expr.type]

            self.__printf(f"{_fmt}", "print.cte", _addr)  # FIXME use value for non-strings

        elif isinstance(node.expr, ExprList):
            _fmt, _fmt_args = [], []
            for expr in node.expr:
                if isinstance(expr, Constant):
                    _value = self.visit(expr)
                    _fmt.append(_fmt_dict[expr.type])
                    if expr.type == TYPE_STRING.typename:
                        _addr = self.__global_const("print.arg", _value)
                        _fmt_args.append(_addr)
                    else:
                        _fmt_args.append(_value)

                elif isinstance(expr, ArrayRef):
                    _value = self.visit(expr)
                    _fmt.append(_fmt_dict["int"]) # FIXME expr.type])
                    _fmt_args.append(_value)

                else:
                    assert False

            self.__printf(f"{''.join(_fmt)}", "print.lst", *_fmt_args)

        else:
            assert False

    def visit_Program(self, node: Program):
        for gdecl in node.gdecls:
            self.visit(gdecl)

    def visit_PtrDecl(self, node: PtrDecl): raise NotImplementedError

    def visit_Read(self, node: Read): raise NotImplementedError

    def visit_Return(self, node: Return):

        if node.expr is not None:
            fn_return_value = self.visit(node.expr)
            self.builder.store(fn_return_value, self.func_return_addr)

        self.__terminate(target=self.func_exit_block)

    def visit_Type(self, node: Type):
        pass

    def visit_VarDecl(self, node: VarDecl):
        self.visit(node.type)

    def visit_UnaryOp(self, node: UnaryOp):

        expr_value = self.visit(node.expr)
        expr_addr = None if not isinstance(node.expr, ID) else self.__addr(node.expr.name)  # FIXME arrays

        if node.op.startswith('p'):
            self.__unop(node.op, expr_value, expr_addr)
            return expr_value
        else:
            return self.__unop(node.op, expr_value, expr_addr)

    def visit_While(self, node: While):
        # Start insertion onto the current block
        self.builder.position_at_end(block=self.builder.block)

        # Create basic blocks in the current function to express the control flow
        cond_bb = ir.Block(self.builder.function, "while.cond")
        body_bb = ir.Block(self.builder.function, "while.body")
        end_bb = ir.Block(self.builder.function, "while.end")

        self.loop_end_blocks.append(end_bb)

        # Condition:
        self.builder.branch(target=cond_bb)
        self.builder.function.basic_blocks.append(cond_bb)
        self.builder.position_at_start(block=cond_bb)

        cond_value = self.visit(node.cond)
        self.builder.cbranch(cond=cond_value, truebr=body_bb, falsebr=end_bb)

        # Body:
        self.builder.function.basic_blocks.append(body_bb)
        self.builder.position_at_start(block=body_bb)

        self.visit(node.body)
        self.__terminate(target=cond_bb)

        # End:
        self.builder.function.basic_blocks.append(end_bb)
        self.builder.position_at_start(block=end_bb)
        self.loop_end_blocks.pop()

###########################################################
## uC's LLVM IR Helper ####################################
###########################################################

class UCLLVM:
    class Type:
        Int = ir.IntType(32)
        Float = ir.DoubleType()
        Char = ir.IntType(8)
        # String = Char.as_pointer()  # FIXME ir.ArrayType(Char, count=) maybe (?)
        Bool = ir.IntType(1)
        Void = ir.VoidType()

        @staticmethod
        def of(typename: List[str]):
            try:
                basename, *qualifiers = typename  # FIXME arrays/strings
                return {
                    TYPE_INT.typename: UCLLVM.Type.Int,
                    TYPE_FLOAT.typename: UCLLVM.Type.Float,
                    TYPE_CHAR.typename: UCLLVM.Type.Char,
                    TYPE_VOID.typename: UCLLVM.Type.Void,
                    TYPE_BOOL.typename: UCLLVM.Type.Bool,
                }[basename]
            except KeyError:
                assert False, f"Type name not mapped to an LLVM type: '{typename}'"

    class Const:
        # Int
        i0 = ir.Constant(ir.IntType(32), 0)
        i1 = ir.Constant(ir.IntType(32), 1)

        # Float
        f0 = ir.Constant(ir.DoubleType(), 0)
        f1 = ir.Constant(ir.DoubleType(), 1)

        # Char
        c0 = ir.Constant(ir.IntType(8), 0)

        # Bool
        true = ir.Constant(ir.DoubleType(), 1)
        false = ir.Constant(ir.DoubleType(), 0)

        @staticmethod
        def zero(ir_type: ir.Type) -> ir.Constant:
            return {
                UCLLVM.Type.Int: UCLLVM.Const.i0,
                UCLLVM.Type.Float: UCLLVM.Const.f0,
                UCLLVM.Type.Char: UCLLVM.Const.c0,
                UCLLVM.Type.Void: None,
                UCLLVM.Type.Bool: UCLLVM.Const.false,
            }[ir_type]
