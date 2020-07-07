from typing import Dict

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

        # Current function IR builder and symbol table
        self.func_builder: ir.IRBuilder = None
        self.func_symtab: Dict[str, ir.AllocaInstr] = {}

        # Global IR builder and symbol table
        self.global_builder: ir.IRBuilder = None  # XXX may not be needed (?)
        self.global_symtab: Dict[str, ir.AllocaInstr] = {}

    def generate_code(self, node: Node):
        assert isinstance(node, Program)
        return self.visit(node)

    def __alloca(self, var_name: str, ir_type: ir.Type) -> ir.AllocaInstr:
        ''' Create an alloca instruction in the entry block of the current function. '''
        size = None  # FIXME add as arg for implementing arrays/strings

        if self.func_builder is not None:
            with self.func_builder.goto_entry_block():
                var_addr = self.builder.alloca(typ=ir_type, size=size, name=f"{var_name}.addr")
                self.func_symtab[var_name] = var_addr
        else:
            # NOTE assume it's a global variable
            var_addr = ir.GlobalVariable(self.module, typ=ir_type, name=var_name)
            self.global_symtab[var_name] = var_addr

        return var_addr

    def visit_ArrayDecl(self, node: ArrayDecl): raise NotImplementedError  # [type*, dim*]
    def visit_ArrayRef(self, node: ArrayRef): raise NotImplementedError  # [name*, subscript*]
    def visit_Assert(self, node: Assert): raise NotImplementedError  # [expr*]
    def visit_Assignment(self, node: Assignment): raise NotImplementedError  # [op, lvalue*, rvalue*]
    def visit_BinaryOp(self, node: BinaryOp): raise NotImplementedError  # [op, left*, right*]
    def visit_Break(self, node: Break): raise NotImplementedError  # []
    def visit_Cast(self, node: Cast): raise NotImplementedError  # [type*, expr*]

    def visit_Compound(self, node: Compound):  # [decls**, stmts**]
        for decl in node.decls or []:
            self.visit(decl)
        for stmt in node.stmts or []:
            self.visit(stmt)

    def visit_Constant(self, node: Constant):  # [type, value]
        # FIXME global constants
        _ass(isinstance(node.type, Type))
        return ir.Constant(typ=UCLLVM.Type.of(node.type.names), constant=node.value)  # FIXME add \00 to strings

    def visit_Decl(self, node: Decl):  # [name*, type*, init*]
        _ass(isinstance(node.name, ID))
        _ass(isinstance(node.type, (ArrayDecl, FuncDecl, PtrDecl, VarDecl)))
        _ass(isinstance(node.type.type, Type))
        _log(f"visiting Decl, type(node.init)={type(node.init)}")

        if isinstance(node.type, VarDecl):
            # FIXME global variables
            var_addr = self.__alloca(var_name=node.name.name, ir_type=UCLLVM.Type.of(node.type.type.names))
            # TODO call a builder to store the init value on var_addr

        elif isinstance(node.type, FuncDecl):
            self.func_symtab = {}
            pass  # FIXME functions
        elif isinstance(node.type, ArrayDecl):
            pass  # FIXME arrays
        elif isinstance(node.type, PtrDecl):
            raise NotImplementedError

    def visit_DeclList(self, node: DeclList): raise NotImplementedError  # [decls**]
    def visit_EmptyStatement(self, node: EmptyStatement): raise NotImplementedError  # []
    def visit_ExprList(self, node: ExprList): raise NotImplementedError  # [exprs**]
    def visit_For(self, node: For): raise NotImplementedError  # [init*, cond*, next*, body*]
    def visit_FuncCall(self, node: FuncCall): raise NotImplementedError  # [name*, args*]
    def visit_FuncDecl(self, node: FuncDecl): raise NotImplementedError  # [args*, type*]
    def visit_FuncDef(self, node: FuncDef): raise NotImplementedError  # [spec*, decl*, body*]

    def visit_GlobalDecl(self, node: GlobalDecl):  # [decls**]
        for decl in node.decls:
            self.visit(decl)  # XXX add a 'global?' attr

    def visit_ID(self, node: ID):  # [name]
        var_addr = self.func_symtab.get(node.name) or self.global_symtab[node.name]
        return self.func_builder.load(ptr=var_addr, name=node.name)

    def visit_If(self, node: If): raise NotImplementedError  # [cond*, ifthen*, ifelse*]
    def visit_InitList(self, node: InitList): raise NotImplementedError  # [exprs**]
    def visit_ParamList(self, node: ParamList): raise NotImplementedError  # [params**]
    def visit_Print(self, node: Print): raise NotImplementedError  # [expr*]

    def visit_Program(self, node: Program):  # [gdecls**]
        for gdecl in node.gdecls:
            self.visit(gdecl)

    def visit_PtrDecl(self, node: PtrDecl):  # [type*]
        raise NotImplementedError

    def visit_Read(self, node: Read): raise NotImplementedError  # [expr*]
    def visit_Return(self, node: Return): raise NotImplementedError  # [expr*]

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

        def of(typename: str):
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

    # class Const:
    #     i0 = ir.Constant(UCLLVM.Type.Int, 0)
    #     i1 = ir.Constant(UCLLVM.Type.Int, 1)

    #     f0 = ir.Constant(UCLLVM.Type.Float, 0)
    #     f1 = ir.Constant(UCLLVM.Type.Float, 1)

    #     true = ir.Constant(UCLLVM.Type.Bool, 1)
    #     false = ir.Constant(UCLLVM.Type.Bool, 0)
