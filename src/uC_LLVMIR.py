from typing import Dict

import llvmlite.ir as ir

from uC_AST import *

###########################################################
## uC to LLVM IR ##########################################
###########################################################


class LLVMCodeGenerator(NodeVisitor):
    ''' Node visitor class that creates LLVM IR code. '''

    def __init__(self) -> None:
        super(LLVMCodeGenerator, self).__init__()

        self.module: ir.Module = ir.Module()
        self.builder: ir.IRBuilder = None

        self.func_symtab: Dict[str, ir.AllocaInstr] = {}
        self.global_symtab: Dict[str, ir.AllocaInstr] = {}

    def generate_code(self, node: Node):
        assert isinstance(node, Program)
        return self.visit(node)

    def __alloca(self, var_name: str) -> ir.AllocaInstr:
        """ Create an alloca instruction in the entry block of the current function. """
        with self.builder.goto_entry_block():
            var_addr = self.builder.alloca(typ=ir.DoubleType(), size=None, name=f"{var_name}.addr")
        return var_addr

    def visit_ArrayDecl(self, node: ArrayDecl): raise NotImplementedError  # [type*, dim*]
    def visit_ArrayRef(self, node: ArrayRef): raise NotImplementedError  # [name*, subscript*]
    def visit_Assert(self, node: Assert): raise NotImplementedError  # [expr*]
    def visit_Assignment(self, node: Assignment): raise NotImplementedError  # [op, lvalue*, rvalue*]
    def visit_BinaryOp(self, node: BinaryOp): raise NotImplementedError  # [op, left*, right*]
    def visit_Break(self, node: Break): raise NotImplementedError  # []
    def visit_Cast(self, node: Cast): raise NotImplementedError  # [type*, expr*]
    def visit_Compound(self, node: Compound): raise NotImplementedError  # [decls**, stmts**]
    def visit_Constant(self, node: Constant): raise NotImplementedError  # [type, value]
    def visit_Decl(self, node: Decl): raise NotImplementedError  # [name*, type*, init*]
    def visit_DeclList(self, node: DeclList): raise NotImplementedError  # [decls**]
    def visit_EmptyStatement(self, node: EmptyStatement): raise NotImplementedError  # []
    def visit_ExprList(self, node: ExprList): raise NotImplementedError  # [exprs**]
    def visit_For(self, node: For): raise NotImplementedError  # [init*, cond*, next*, body*]
    def visit_FuncCall(self, node: FuncCall): raise NotImplementedError  # [name*, args*]
    def visit_FuncDecl(self, node: FuncDecl): raise NotImplementedError  # [args*, type*]
    def visit_FuncDef(self, node: FuncDef): raise NotImplementedError  # [spec*, decl*, body*]
    def visit_GlobalDecl(self, node: GlobalDecl): raise NotImplementedError  # [decls**]
    def visit_ID(self, node: ID): raise NotImplementedError  # [name]
    def visit_If(self, node: If): raise NotImplementedError  # [cond*, ifthen*, ifelse*]
    def visit_InitList(self, node: InitList): raise NotImplementedError  # [exprs**]
    def visit_ParamList(self, node: ParamList): raise NotImplementedError  # [params**]
    def visit_Print(self, node: Print): raise NotImplementedError  # [expr*]
    def visit_Program(self, node: Program): raise NotImplementedError  # [gdecls**]
    def visit_PtrDecl(self, node: PtrDecl): raise NotImplementedError  # [type*]
    def visit_Read(self, node: Read): raise NotImplementedError  # [expr*]
    def visit_Return(self, node: Return): raise NotImplementedError  # [expr*]
    def visit_Type(self, node: Type): raise NotImplementedError  # [names]
    def visit_VarDecl(self, node: VarDecl): raise NotImplementedError  # [declname, type*]
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
        Bool = ir.IntType(1)
        Void = ir.VoidType()

    class Const:
        i0 = ir.Constant(Type.Int, 0)
        i1 = ir.Constant(Type.Int, 1)

        f0 = ir.Constant(Type.Float, 0)
        f1 = ir.Constant(Type.Float, 1)

        true = ir.Constant(Type.Bool, 1)
        false = ir.Constant(Type.Bool, 0)
