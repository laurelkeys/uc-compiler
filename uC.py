#
# This is the main program for the uC compiler, which just parses command-line options, figures
# out which source files to read and write to, and invokes the different stages of the compiler.
#
# One of the most important parts of writing a compiler is reliable reporting of error messages back to the user.
# This file defines some generic functionality for dealing with errors throughout the compiler project.
#

import __context_root__

import sys

from uC_errors import error, errors_reported, clear_errors, subscribe_errors

from uC_parser import UCParser
from uC_sema import Visitor
from uC_IR import GenerateCode, Instruction
from uC_CFG import ControlFlowGraph, GraphViewer
from uC_DFA import DataFlow
from uC_opt import Optimizer
from uc_interpreter import Interpreter

###########################################################
## uC Compiler ############################################
###########################################################


class Compiler:
    ''' This object encapsulates the compiler and serves as a facade interface for the compiler itself. '''

    def __init__(self):
        self.total_errors = 0
        self.total_warnings = 0

    def _parse(self, susy, ast_file, debug):
        ''' Parses the source code.\n
            If `ast_file` is not `None`, prints out the abstract syntax tree (AST).
        '''
        self.parser = UCParser()
        self.ast = self.parser.parse(self.code, "", debug)

    def _sema(self, susy, ast_file):
        ''' Decorate the AST with semantic actions.\n
            If `ast_file` is not `None`, prints out the abstract syntax tree (AST). '''
        try:
            self.sema = Visitor()
            self.sema.visit(self.ast)
            if not susy and ast_file is not None:
                self.ast.show(buf=ast_file, showcoord=True)
        except AssertionError as e:
            error(None, e)

    def _gencode(self, susy, ir_file):
        ''' Generate uCIR code for the decorated AST. '''
        self.gen = GenerateCode()
        self.gen.visit(self.ast)
        self.gencode = self.gen.code

        ## FIXME
        ## if not susy and ir_file is not None:
        ##     self.gen.show(buf=ir_file)

        print("----")  # FIXME debug only
        self.gen.show(show_lines=True)
        print("----")

        if not susy and ir_file is not None:
            _str = ""
            for _code in self.gencode:
                _str += f"{_code}\n"
            ir_file.write(_str)

    def _opt(self, susy, opt_file, emit_cfg, debug):
        ''' Optimize the generated uCIR code. '''
        self.cfg = ControlFlowGraph(self.gencode)

        # NOTE the graph is being plotted after simplifying
        self.cfg.simplify()
        if emit_cfg:
            for entry_name, entry_block in self.cfg.entries.items():
                GraphViewer.view_entry(entry_name, entry_block, save_as_png=True)

        changed = True
        while changed:
            lines_before = len(self.cfg.build_code())

            Optimizer.constant_folding_and_propagation(self.cfg)
            Optimizer.dead_code_elimination(self.cfg)
            self.cfg.simplify()

            changed = len(self.cfg.build_code()) != lines_before

        Optimizer.post_process_blocks(self.cfg)

        ##
        self.optcode = self.cfg.build_code()

        print("----")
        print("\n".join(Instruction.prettify(self.optcode)))
        print("Lines Before:", len(self.gencode))
        print("Lines After :", len(self.optcode))
        ##

        # TODO stuff..

    def _do_compile(self, susy, ast_file, ir_file, opt_file, opt, emit_cfg, debug):
        ''' Compiles the code to the given file object. '''
        self._parse(susy, ast_file, debug)
        if not errors_reported():
            self._sema(susy, ast_file)
        if not errors_reported():
            self._gencode(susy, ir_file)
            if opt:
                self._opt(susy, opt_file, emit_cfg, debug)

    def compile(self, code, susy, ast_file, ir_file, opt_file, opt, run_ir, emit_cfg, debug):
        ''' Compiles the given code string. '''
        self.code = code
        with subscribe_errors(lambda msg: sys.stderr.write(msg + "\n")):
            self._do_compile(susy, ast_file, ir_file, opt_file, opt, emit_cfg, debug)
            if errors_reported():
                sys.stderr.write("{} error(s) encountered.".format(errors_reported()))
            else:
                # FIXME
                # if opt:
                #     self.speedup = len(self.gencode) / len(self.optcode)
                #     sys.stderr.write(
                #         "original = %d, otimizado = %d, speedup = %.2f\n"
                #         % (len(self.gencode), len(self.optcode), self.speedup)
                #     )
                if run_ir:
                    print("----")
                    self.vm = Interpreter()
                    # self.vm.run(self.gencode)
                    # FIXME
                    if opt:
                        self.vm.run(self.optcode)
                    else:
                        self.vm.run(self.gencode)
        return 0


def run_compiler():
    ''' Runs the command-line compiler. '''

    if len(sys.argv) < 2:
        print(
            "Usage: python uC.py <source-file> [-at-susy] [-no-ast] [-no-ir] [-no-run] [-cfg] [-opt] [-debug]"
        )
        sys.exit(1)

    emit_cfg = False
    emit_ast = True
    emit_ir = True
    run_ir = True
    susy = False
    opt = True  # FIXME set to False by default
    debug = False

    params = sys.argv[1:]
    files = sys.argv[1:]

    for param in params:
        if param[0] == "-":
            if param == "-no-ast":
                emit_ast = False
            elif param == "-no-ir":
                emit_ir = False
            elif param == "-at-susy":
                susy = True
            elif param == "-no-run":
                run_ir = False
            elif param in ["-cfg", "-g"]:
                emit_cfg = True
            elif param == "-opt":
                opt = True
            elif param == "-debug":
                debug = True
            else:
                print("Unknown option: %s" % param)
                sys.exit(1)
            files.remove(param)

    for file in files:
        if file[-3:] == ".uc":
            source_filename = file
        else:
            source_filename = file + ".uc"

        open_files = []

        ast_file = None
        if emit_ast and not susy:
            ast_filename = source_filename[:-3] + ".ast"
            print("Outputting the AST to %s." % ast_filename)
            ast_file = open(ast_filename, "w")
            open_files.append(ast_file)

        ir_file = None
        if emit_ir and not susy:
            ir_filename = source_filename[:-3] + ".ir"
            print("Outputting the uCIR to %s." % ir_filename)
            ir_file = open(ir_filename, "w")
            open_files.append(ir_file)

        opt_file = None
        if opt and not susy:
            opt_filename = source_filename[:-3] + ".opt"
            print("Outputting the optimized uCIR to %s." % opt_filename)
            opt_file = open(opt_filename, "w")
            open_files.append(opt_file)

        source = open(source_filename, "r")
        code = source.read()
        source.close()

        retval = Compiler().compile(
            code, susy, ast_file, ir_file, opt_file, opt, run_ir, emit_cfg, debug
        )
        for f in open_files:
            f.close()
        if retval != 0:
            sys.exit(retval)

    sys.exit(retval)


if __name__ == "__main__":
    run_compiler()


# NOTE The utility function `errors_reported()` returns the total number of errors reported so far.
#      Different stages of the compiler might use this to decide whether or not to keep processing or not.
#      Use `clear_errors()` to clear the total number of errors.

# NOTE Error handling is based on a subscription based model using context-managers and the `subscribe_errors()` function.
#
#      For example, to route error messages to standard output, use this:
#          with subscribe_errors(print):
#              run_compiler()
#
#      To send messages to standard error, you can do this:
#          from functools import partial
#          with subscribe_errors(partial(print, file=sys.stderr)):
#               run_compiler()
#
#      To route messages to a logger, you can do this:
#          import logging
#          log = logging.getLogger("somelogger")
#          with subscribe_errors(log.error):
#               run_compiler()
#
#      To collect error messages for the purpose of unit testing, do this:
#          errs = []
#          with subscribe_errors(errs.append):
#               run_compiler()
#          # Check errs for specific errors
