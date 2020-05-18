#
# This is the main program for the uC compiler, which just parses command-line options, figures
# out which source files to read and write to, and invokes the different stages of the compiler.
#
# One of the most important parts of writing a compiler is reliable reporting of error messages back to the user.
# This file defines some generic functionality for dealing with errors throughout the compiler project.
#

import sys

from contextlib import contextmanager

from uc_parser import UCParser
from uc_sema import Visitor
from uc_ir import GenerateCode
from uc_interpreter import Interpreter

###########################################################
## uC Error Handling Helper ###############################
###########################################################

_subscribers = []
_num_errors = 0

def error(lineno, message, filename=None):
    ''' Report a compiler error to all subscribers. '''
    global _num_errors
    if not filename:
        if not lineno:
            errmsg = "{}".format(message)
        else:
            errmsg = "{}: {}".format(lineno, message)
    else:
        if not lineno:
            errmsg = "{}: {}".format(filename, message)
        else:
            errmsg = "{}:{}: {}".format(filename, lineno, message)
    for subscriber in _subscribers:
        subscriber(errmsg)
    _num_errors += 1

def errors_reported():
    ''' Return the number of errors reported. '''
    return _num_errors

def clear_errors():
    ''' Reset the total number of errors reported to 0. '''
    global _num_errors
    _num_errors = 0

@contextmanager
def subscribe_errors(handler):
    ''' Context manager that allows monitoring of compiler error messages.\n
        Use as follows, where `handler` is a callable taking a single argument which is the error message string:
        ```
        with subscribe_errors(handler):
            # ... do compiler ops ...
        ```
    '''
    _subscribers.append(handler)
    try:
        yield
    finally:
        _subscribers.remove(handler)

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
        self.ast = self.parser.parse(self.code, '', debug)

    def _sema(self, susy, ast_file):
        ''' Decorate the AST with semantic actions.\n
            If `ast_file` is not `None`, prints out the abstract syntax tree (AST). '''
        try:
            self.sema = Visitor()
            self.sema.visit(self.ast)
            if susy:
                self.ast.show(showcoord=True)
            elif ast_file is not None:
                self.ast.show(buf=ast_file, showcoord=True)
        except AssertionError as e:
            error(None, e)

    def _gencode(self, susy, ir_file):
        ''' Generate uCIR Code for the decorated AST. '''
        self.gen = GenerateCode()
        self.gen.visit(self.ast)
        self.gencode = self.gen.code
        _str = ""
        for _code in self.gencode:
            print(_code)
        if not susy and ir_file is not None:
            for _code in self.gencode:
                _str += f"{_code}\n"
            ir_file.write(_str)

    def _do_compile(self, susy, ast_file, ir_file, debug):
        ''' Compiles the code to the given file object. '''
        self._parse(susy, ast_file, debug)
        if not errors_reported():
            self._sema(susy, ast_file)
        if not errors_reported():
            self._gencode(susy, ir_file)

    def compile(self, code, susy, ast_file, ir_file, run_ir, debug):
        ''' Compiles the given code string. '''
        self.code = code
        with subscribe_errors(lambda msg: sys.stderr.write(msg + "\n")):
            self._do_compile(susy, ast_file, debug, ir_file)
            if errors_reported():
                sys.stderr.write("{} error(s) encountered.".format(errors_reported()))
            elif run_ir:
                self.vm = Interpreter()
                self.vm.run(self.gencode)
        return 0


def run_compiler():
    ''' Runs the command-line compiler. '''

    if len(sys.argv) < 2:
        print("Usage: python uC.py <source-file> [-at-susy] [-no-ir] [-no-run] [-no-ast] [-debug]")
        sys.exit(1)

    emit_ast = True
    emit_ir = True
    run_ir = True
    susy = False
    debug = False

    params = sys.argv[1:]
    files = sys.argv[1:]

    for param in params:
        if param[0] == '-':
            if param == '-no-ast':
                emit_ast = False
            elif param == '-no-ir':
                emit_ir = False
            elif param == '-at-susy':
                susy = True
            elif param == '-no-run':
                run_ir = False
            elif param == '-debug':
                debug = True
            else:
                print("Unknown option: %s" % param)
                sys.exit(1)
            files.remove(param)

    for file in files:
        if file[-3:] == '.uc':
            source_filename = file
        else:
            source_filename = file + '.uc'

        open_files = []

        ast_file = None
        if emit_ast and not susy:
            ast_filename = source_filename[:-3] + '.ast'
            print("Outputting the AST to %s." % ast_filename)
            ast_file = open(ast_filename, 'w')
            open_files.append(ast_file)

        ir_file = None
        if emit_ir and not susy:
            ir_filename = source_filename[:-3] + '.ir'
            print("Outputting the uCIR to %s." % ir_filename)
            ir_file = open(ir_filename, 'w')
            open_files.append(ir_file)

        source = open(source_filename, 'r')
        code = source.read()
        source.close()

        retval = Compiler().compile(code, susy, ast_file, ir_file, run_ir, debug)
        for f in open_files:
            f.close()
        if retval != 0:
            sys.exit(retval)

    sys.exit(retval)


if __name__ == '__main__':
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
