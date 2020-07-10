from typing import Dict, List

import llvmlite.ir as ir

from uC_AST import *
from uC_types import *

###########################################################
## uC to LLVM IR ##########################################
###########################################################

def _log(*a, **k):
    print("[log]", *a, **k)

def _ass(cond):
    assert cond

class LLVMCodeGenerator(NodeVisitor):
    ''' Node visitor class that creates LLVM IR code. '''

    def __init__(self) -> None:
        super(LLVMCodeGenerator, self).__init__()

        # Top-level container of all other LLVM IR objects
        self.module: ir.Module = ir.Module()

        # Current IR builder
        self.builder: ir.IRBuilder = None

        # Global and current function symbol tables
        self.func_symtab: Dict[str, ir.AllocaInstr] = {}
        self.global_symtab: Dict[str, ir.AllocaInstr] = {}

    def generate_code(self, node: Node) -> str:
        assert isinstance(node, Program)
        self.visit(node)
        return str(self.module)

    def __addr(self, var_name: str) -> ir.AllocaInstr:
        ''' Return the address pointed by `var_name`. '''
        return self.func_symtab.get(var_name) or self.global_symtab[var_name]

    def __alloca(self, var_name: str, ir_type: ir.Type) -> ir.AllocaInstr:
        ''' Create an alloca instruction in the entry block of the current function,
            if there is one, or in global scope (and add it to the correct symtab).
        '''
        size = None  # FIXME add as arg for implementing arrays/strings

        if self.builder is not None:
            with self.builder.goto_entry_block():
                var_addr = self.builder.alloca(typ=ir_type, size=size, name=f"{var_name}.addr")
                assert var_name not in self.func_symtab  # NOTE sanity check
                self.func_symtab[var_name] = var_addr
        else:
            # NOTE assume it's a global variable
            var_addr = ir.GlobalVariable(self.module, typ=ir_type, name=var_name)
            assert var_name not in self.global_symtab  # NOTE sanity check
            self.global_symtab[var_name] = var_addr

        return var_addr

    def __binop(self, binop: str, lhs: ir.Value, rhs: ir.Value) -> ir.Value:
        ''' Return the equivalent of `lhs <binop> rhs`, abstracting type-handling. '''
        assert isinstance(lhs, type(rhs)), f"{type(lhs)} != {type(rhs)}"

        if isinstance(lhs.type, ir.IntType):
            assert binop in TYPE_INT.binary_ops, binop
            return {
                '+': lambda: self.builder.add(lhs, rhs, name="iadd"),
                '-': lambda: self.builder.sub(lhs, rhs, name="isub"),
                '*': lambda: self.builder.mul(lhs, rhs, name="imul"),
                '/': lambda: self.builder.sdiv(lhs, rhs, name="idiv"),
                '%': lambda: self.builder.srem(lhs, rhs, name="irem"),
            }[binop]()

        elif isinstance(lhs.type, ir.DoubleType):
            assert binop in TYPE_FLOAT.binary_ops, binop
            return {
                '+': lambda: self.builder.fadd(lhs, rhs, name="fadd"),
                '-': lambda: self.builder.fsub(lhs, rhs, name="fsub"),
                '*': lambda: self.builder.fmul(lhs, rhs, name="fmul"),
                '/': lambda: self.builder.fdiv(lhs, rhs, name="fdiv"),
                '%': lambda: self.builder.frem(lhs, rhs, name="frem"),
            }[binop]()

        else:
            assert False, type(lhs)  # TODO implement

    def __byte_array(self, source, convert_str=True) -> ir.Constant:
        b = bytearray(source) if not convert_str else (source + '\00').encode('ascii')
        n = len(b)
        return ir.Constant(ir.ArrayType(UCLLVM.Type.Char, n), b)

    def visit_ArrayDecl(self, node: ArrayDecl):  # [type*, dim*]
        raise NotImplementedError

    def visit_ArrayRef(self, node: ArrayRef):  # [name*, subscript*]
        raise NotImplementedError

    def visit_Assert(self, node: Assert):  # [expr*]
        # TODO implement
        raise NotImplementedError


    def visit_Assignment(self, node: Assignment):  # [op, lvalue*, rvalue*]
        _log(f"visiting Assignment, type(node.lvalue)={type(node.lvalue)}")
        _log(f"visiting Assignment, type(node.rvalue)={type(node.rvalue)}")

        if isinstance(node.lvalue, ID):
            lhs_addr = self.__addr(node.lvalue.name)
        else:
            assert False, node.lvalue  # TODO implement

        rhs_value = self.visit(node.rvalue)

        if node.op != "=":
            assert len(node.op) == 2, node.op
            _log(f"visiting Assignment, node.op={node.op}")
            lhs_value = self.builder.load(ptr=lhs_addr, name=node.lvalue.name)
            rhs_value = self.__binop(binop=node.op[0], lhs=lhs_value, rhs=rhs_value)

        self.builder.store(value=rhs_value, ptr=lhs_addr)
        return rhs_value

    def visit_BinaryOp(self, node: BinaryOp):  # [op, left*, right*]
        _log(f"visiting Assignment, type(node.left)={type(node.left)}")
        _log(f"visiting Assignment, type(node.right)={type(node.right)}")

        lhs_value = self.visit(node.left)
        rhs_value = self.visit(node.right)

        return self.__binop(node.op, lhs_value, rhs_value)

    def visit_Break(self, node: Break): raise NotImplementedError  # []
    def visit_Cast(self, node: Cast): raise NotImplementedError  # [type*, expr*]

    def visit_Compound(self, node: Compound):  # [decls**, stmts**]
        for decl in node.decls or []:
            self.visit(decl)
        for stmt in node.stmts or []:
            self.visit(stmt)

    def visit_Constant(self, node: Constant):  # [type, value]
        # FIXME global constants
        _ass(isinstance(node.type, str))
        return ir.Constant(typ=UCLLVM.Type.of([node.type]), constant=node.value)  # FIXME add \00 to strings

    def visit_Decl(self, node: Decl):  # [name*, type*, init*]
        _ass(isinstance(node.name, ID))
        _ass(isinstance(node.type, (ArrayDecl, FuncDecl, PtrDecl, VarDecl)))
        _log(f"visiting Decl, type(node.init)={type(node.init)}")

        name = node.name.name

        if isinstance(node.type, FuncDecl):
            _ass(node.init is None)
            _ass(isinstance(node.type.type, VarDecl))
            _ass(isinstance(node.type.type.type, Type))
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
                    _ass(isinstance(arg_decl, Decl))
                    _ass(isinstance(arg_decl.type, VarDecl))
                    arg.name = arg_decl.name
            else:
                # Assert that all we've seen is the function's prototype
                assert isinstance(fn, ir.Function), f"Function/global name collision '{fn_name}'"
                assert fn.is_declaration, f"Redefinition of '{fn_name}'"
                assert len(fn.function_type.args) == len(fn_type.args), (
                    f"Definition of '{fn_name}' with wrong argument count"
                )

            return fn

        elif isinstance(node.type, VarDecl):
            _ass(node.init is None)
            _ass(isinstance(node.type.type, Type))
            vardecl: VarDecl = node.type

            # Allocate space for the variable (and register it in the correct symtab)
            var_name = name
            var_addr = self.__alloca(var_name, ir_type=UCLLVM.Type.of(vardecl.type.names))

            # Store its optional initial value
            if node.init is not None:
                init_value = self.visit(node.init)  # FIXME this could be a name (or an addr)
                self.builder.store(value=init_value, ptr=var_addr)
            else:
                # TODO zero-initialize (needs a "zero" for each type)
                init_value = None

            return init_value  # FIXME what do we need to return, actually? i.e. name/addr/value

        elif isinstance(node.type, ArrayDecl):
            pass  # TODO arrays

        elif isinstance(node.type, PtrDecl):
            raise NotImplementedError

    def visit_DeclList(self, node: DeclList): raise NotImplementedError  # [decls**]

    def visit_EmptyStatement(self, node: EmptyStatement):  # []
        _log(f"visiting EmptyStatement, node={node}")
        pass

    def visit_ExprList(self, node: ExprList): raise NotImplementedError  # [exprs**]
    def visit_For(self, node: For): raise NotImplementedError  # [init*, cond*, next*, body*]
    def visit_FuncCall(self, node: FuncCall): raise NotImplementedError  # [name*, args*]

    def visit_FuncDecl(self, node: FuncDecl): raise NotImplementedError  # [args*, type*]

    def visit_FuncDef(self, node: FuncDef):  # [spec*, decl*, body*]
        _ass(isinstance(node.spec, Type))
        _ass(isinstance(node.decl, Decl))
        _ass(isinstance(node.body, Compound))  # TODO double check for empty/single-line functions

        # Reset the current function symbol table
        self.func_symtab = {}

        # Generate an ir.Function from the prototype (i.e. the function declaration)
        fn: ir.Function = self.visit(node.decl)

        # Create a new basic block to start insertion into
        bb_entry = fn.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block=bb_entry)

        # Add the function arguments to the stack (and the symbol table)
        for arg in fn.args:
            arg_addr = self.__alloca(var_name=arg.name, ir_type=arg.type)
            self.builder.store(value=arg, ptr=arg_addr)

        # Finish off generating the function
        self.visit(node.body)
        self.builder = None

        return fn

    def visit_GlobalDecl(self, node: GlobalDecl):  # [decls**]
        for decl in node.decls:
            self.visit(decl)  # XXX add a 'global?' attr

    def visit_ID(self, node: ID):  # [name]
        var_addr = self.__addr(node.name)
        return self.builder.load(ptr=var_addr, name=node.name)

    def visit_If(self, node: If): raise NotImplementedError  # [cond*, ifthen*, ifelse*]
    def visit_InitList(self, node: InitList): raise NotImplementedError  # [exprs**]
    def visit_ParamList(self, node: ParamList): raise NotImplementedError  # [params**]

    def visit_Print(self, node: Print):  # [expr*]
        raise NotImplementedError

    def visit_Program(self, node: Program):  # [gdecls**]
        for gdecl in node.gdecls:
            self.visit(gdecl)

    def visit_PtrDecl(self, node: PtrDecl):  # [type*]
        raise NotImplementedError

    def visit_Read(self, node: Read): raise NotImplementedError  # [expr*]

    def visit_Return(self, node: Return):  # [expr*]
        _log(f"visiting Return, type(node.expr)={type(node.expr)}")
        fn_return_value = self.visit(node.expr)
        self.builder.ret(fn_return_value)

    def visit_Type(self, node: Type):  # [names]
        _log(f"visiting Type, node={node}")
        pass

    def visit_VarDecl(self, node: VarDecl):  # [declname, type*]
        _ass(isinstance(node.type, Type))
        self.visit(node.type)

    def visit_UnaryOp(self, node: UnaryOp): raise NotImplementedError  # [op, expr*]
    def visit_While(self, node: While): raise NotImplementedError  # [cond*, body*]

###########################################################
## uC LLVM Helper #########################################
###########################################################


class UCLLVM:
    class Type:
        Int = ir.IntType(32)
        Float = ir.DoubleType()
        Char = ir.IntType(8)
        # String = Char.as_pointer()  # FIXME ir.ArrayType(Char, count=) maybe (?)
        Bool = ir.IntType(1)
        Void = ir.VoidType()

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

        # Bool
        true = ir.Constant(ir.DoubleType(), 1)
        false = ir.Constant(ir.DoubleType(), 0)
