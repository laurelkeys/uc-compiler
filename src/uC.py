#
# This is the main program for the uC compiler, which just parses command-line options, figures
# out which source files to read and write to, and invokes the different stages of the compiler.
#
# One of the most important parts of writing a compiler is reliable reporting of error messages back to the user.
# This file defines some generic functionality for dealing with errors throughout the compiler project.
#

import sys

from uC_errors import error, errors_reported, subscribe_errors

from uC_parser import UCParser
from uC_sema import Visitor
from uC_IR import GenerateCode, Instruction

###########################################################
## uC Compiler ############################################
###########################################################


class Compiler:
    """ This object encapsulates the compiler and serves as a facade interface for the compiler itself. """

    def __init__(self):
        self.total_errors = 0
        self.total_warnings = 0

    def _parse(self, susy, ast_file):
        """ Parses the source code.\n
            If `ast_file` is not `None`, prints out the abstract syntax tree (AST).
        """
        self.parser = UCParser()
        self.ast = self.parser.parse(self.code, "")  # , self.debug)

    def _sema(self, susy, ast_file):
        """ Decorate the AST with semantic actions.\n
            If `ast_file` is not `None`, prints out the abstract syntax tree (AST). """
        try:
            self.sema = Visitor()
            self.sema.visit(self.ast)
            if not susy and ast_file is not None:
                self.ast.show(buf=ast_file, showcoord=True)
        except AssertionError as e:
            error(None, e)

    def _gencode(self, susy, ir_file):
        """ Generate uCIR code for the decorated AST. """
        self.gen = GenerateCode()
        self.gen.visit(self.ast)
        self.gencode = self.gen.code  # store the unoptimized code

        if not susy and ir_file is not None:
            self.gen.show(buf=ir_file)

        if self.debug:
            print("----")
            self.gen.show()  # print the unoptimized code to stdout

    def _opt(self, susy, opt_file, emit_cfg):
        """ Optimize the generated uCIR code. """
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

        if not susy and opt_file is not None:
            opt_file.write("\n".join(Instruction.prettify(self.optcode)))
            opt_file.write("\n")  # end the file with a newline

        if self.debug:
            print("----")  # print the optimized code to stdout
            print("\n".join(Instruction.prettify(self.optcode)))

        if emit_cfg:
            for entry_name, entry_block in self.cfg.entries.items():
                GraphViewer.view_entry(entry_name, entry_block, save_as_png=True)

    def _do_compile(self, susy, ast_file, ir_file, opt_file, opt, emit_cfg):
        """ Compiles the code to the given file object. """
        self._parse(susy, ast_file)
        if not errors_reported():
            self._sema(susy, ast_file)
        if not errors_reported():
            self._gencode(susy, ir_file)
            if opt:
                self._opt(susy, opt_file, emit_cfg)
            elif emit_cfg:
                self.cfg = ControlFlowGraph(self.gencode)
                for entry_name, entry_block in self.cfg.entries.items():
                    GraphViewer.view_entry(entry_name, entry_block, save_as_png=True)

    def compile(self, code, susy, ast_file, ir_file, opt_file, opt, run_ir, emit_cfg, debug):
        """ Compiles the given code string. """
        self.code = code
        self.debug = debug
        with subscribe_errors(lambda msg: sys.stderr.write(msg + "\n")):
            self._do_compile(susy, ast_file, ir_file, opt_file, opt, emit_cfg)
            if errors_reported():
                sys.stderr.write("{} error(s) encountered.".format(errors_reported()))
            else:
                if opt:
                    if self.debug:
                        print("----")
                    self.speedup = len(self.gencode) / len(self.optcode)
                    sys.stderr.write(
                        "original = %d, otimizado = %d, speedup = %.2f\n"
                        % (len(self.gencode), len(self.optcode), self.speedup)
                    )
                if run_ir:
                    if self.debug:
                        print("----")
                    self.vm = Interpreter()
                    self.vm.run(self.optcode if opt else self.gencode)
        return 0


def run_compiler():
    """ Runs the command-line compiler. """

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
    debug = True  # FIXME set to False by default

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
            elif param in ["-opt", "-o"]:
                opt = not opt  # True
            elif param in ["-debug", "-d"]:
                debug = not debug  # True
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