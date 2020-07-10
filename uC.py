#
# This is the main program for the uC compiler, which just parses command-line options, figures
# out which source files to read and write to, and invokes the different stages of the compiler.
#
# One of the most important parts of writing a compiler is reliable reporting of error messages back to the user.
# This file defines some generic functionality for dealing with errors throughout the compiler project.
#

import __context_root__

import os
import sys
import argparse

from uC_IR import GenerateCode, Instruction
from uC_opt import Optimizer
from uC_CFG import ControlFlowGraph, GraphViewer
from uC_sema import Visitor
from uC_parser import UCParser
from uC_LLVMIR import LLVMCodeGenerator
from uC_LLVMjit import LLVMCompiler
from uC_errors import clear_errors, error, errors_reported, subscribe_errors
from uc_interpreter import Interpreter

###########################################################
## uC Compiler ############################################
###########################################################


class Compiler:
    ''' This object encapsulates the compiler and serves as a facade interface for the compiler itself. '''

    def __init__(self, cli_args):
        self.code = None
        self.total_errors = 0
        self.total_warnings = 0
        self.args = cli_args

    def _parse(self):
        ''' Parses the source code.\n
            If `ast_file is not None`, prints out the abstract syntax tree (AST).
        '''
        self.parser = UCParser()
        self.ast = self.parser.parse(self.code)

        if self.args.debug:
            print("----")
            self.ast.show()  # print the AST to stdout

    def _sema(self):
        ''' Decorate the AST with semantic actions.\n
            If `ast_file is not None`, prints out the abstract syntax tree (AST).
        '''
        try:
            self.sema = Visitor()
            self.sema.visit(self.ast)
            if not self.args.susy and self.ast_file is not None:
                self.ast.show(buf=self.ast_file, showcoord=True)
        except AssertionError as e:
            error(None, e)

    def _codegen(self):
        ''' Generate uCIR code from the AST. '''
        self.gen = GenerateCode()
        self.gen.visit(self.ast)
        self.gencode = self.gen.code # store the unoptimized code

        if not self.args.susy and self.ir_file is not None:
            self.gen.show(buf=self.ir_file)

        if self.args.debug:
            print("----")
            self.gen.show()  # print the unoptimized code to stdout

        if self.args.cfg and not self.args.opt:
            self.cfg = ControlFlowGraph(self.gencode)
            for entry_name, entry_block in self.cfg.entries.items():
                GraphViewer.view_entry(entry_name, entry_block, save_as_png=True)

    def _opt(self):
        ''' Optimize the generated uCIR code. '''
        self.cfg = ControlFlowGraph(self.gencode)
        self.cfg.simplify()

        changed = True
        while changed:
            lines_before = len(self.cfg.build_code())

            Optimizer.constant_folding_and_propagation(self.cfg)
            Optimizer.dead_code_elimination(self.cfg)
            self.cfg.simplify()

            changed = len(self.cfg.build_code()) != lines_before

        Optimizer.post_process_blocks(self.cfg)
        self.cfg.simplify()

        self.optcode = self.cfg.build_code()  # store the optimized code
        self.optcode = Optimizer.post_process_code(self.optcode)

        if not self.args.susy and self.opt_file is not None:
            self.opt_file.write("\n".join(Instruction.prettify(self.optcode)))
            self.opt_file.write("\n")  # end the file with a newline

        if self.args.debug:
            print("----")  # print the optimized code to stdout
            print("\n".join(Instruction.prettify(self.optcode)))

        if self.args.cfg:
            for entry_name, entry_block in self.cfg.entries.items():
                GraphViewer.view_entry(entry_name, entry_block, save_as_png=True)

    def _llvm(self):
        ''' Generate LLVM IR code from the AST. '''
        self.llvmgen = LLVMCodeGenerator()
        self.llvmcode = self.llvmgen.generate_code(self.ast) # store the LLVM IR code

        if not self.args.susy and self.llvm_file is not None:
            self.llvm_file.write(self.llvmcode)

        if self.args.debug:
            print("----")
            print(self.llvmcode) # print the LLVM IR code to stdout

        if self.run:
            llvmjit = LLVMCompiler()
            llvmjit.eval(self.llvmcode, self.args.llvm_opt,
                         self.llvm_opt_file, self.args.debug)

    def _do_compile(self):
        ''' Compiles the code to the given file object. '''
        self._parse()

        if not errors_reported():
            self._sema()

        if not errors_reported():
            self._codegen()
            if self.args.opt: self._opt()
            if self.args.llvm: self._llvm()

    def compile(self):
        ''' Compiles code from the given filename. '''
        filename, _ = os.path.splitext(self.args.filename)

        with open(f"{filename}.uc", 'r') as source:
            self.code = source.read()

        open_files = []
        self.ast_file = None
        self.ir_file = None
        self.opt_file = None
        self.llvm_file = None
        self.llvm_opt_file = None

        if not self.args.susy:
            if self.args.ast:
                ast_filename = f"{filename}.ast"
                sys.stderr.write("Outputting the AST to %s.\n" % ast_filename)
                self.ast_file = open(ast_filename, 'w')
                open_files.append(self.ast_file)
            if self.args.ir:
                ir_filename = f"{filename}.ir"
                sys.stderr.write("Outputting the uCIR to %s.\n" % ir_filename)
                self.ir_file = open(ir_filename, 'w')
                open_files.append(self.ir_file)
            if self.args.opt:
                opt_filename = f"{filename}.opt"
                sys.stderr.write("Outputting the optimized uCIR to %s.\n" % opt_filename)
                self.opt_file = open(opt_filename, 'w')
                open_files.append(self.opt_file)
            if self.args.llvm:
                llvm_filename = f"{filename}.ll"
                sys.stderr.write("Outputting the LLVM IR to %s.\n" % llvm_filename)
                self.llvm_file = open(llvm_filename, 'w')
                open_files.append(self.llvm_file)
            if self.args.llvm_opt:
                llvm_opt_filename = f"{filename}.opt.ll"
                sys.stderr.write("Outputting the optimized LLVM IR to %s.\n" % llvm_opt_filename)
                self.llvm_opt_file = open(llvm_opt_filename, 'w')
                open_files.append(self.llvm_opt_file)

        self.run = not self.args.no_run
        with subscribe_errors(lambda msg: sys.stderr.write(msg + "\n")):
            self._do_compile()
            if errors_reported():
                sys.stderr.write("{} error(s) encountered.".format(errors_reported()))
            elif not self.args.llvm:
                if self.args.opt:
                    speedup = len(self.gencode) / len(self.optcode)
                    sys.stderr.write("original = %d, optimized = %d, speedup = %.2f\n" %
                                     (len(self.gencode), len(self.optcode), speedup))
                if self.run and not self.args.cfg:
                    vm = Interpreter()
                    vm.run(self.optcode if self.args.opt else self.gencode)

        for f in open_files:
            f.close()

        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="uC (micro C) language compiler")

    parser.add_argument("filename", help="path to a .uc file to compile")

    parser.add_argument("-s", "--susy", action="store_true",
                        help="run in the susy machine")
    parser.add_argument("-a", "--ast", action="store_true",
                        help="dump the AST to <filename>.ast")
    parser.add_argument("-i", "--ir", action="store_true",
                        help="dump the uCIR to <filename>.ir")
    parser.add_argument("-o", "--opt", action="store_true",
                        help="optimize the uCIR and dump it to <filename>.opt")
    parser.add_argument("-l", "--llvm", action="store_true",
                        help="generate LLVM IR code and dump it to <filename>.ll")
    parser.add_argument("-p", "--llvm-opt", choices=['ctm', 'dce', 'cfg', 'all'],
                        help="specify which LLVM pass optimizations to enable")
    parser.add_argument("-n", "--no-run", action="store_true",
                        help="do not execute the program")
    parser.add_argument("-c", "--cfg", action="store_true",
                        help="show the CFG for each function in png format")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="print debug information")

    args = parser.parse_args()

    retval = Compiler(args).compile()
    sys.exit(retval)
