#
# This is the main program for the uC compiler, which just parses command-line options, figures
# out which source files to read and write to, and invokes the different stages of the compiler.
#   
# One of the most important parts of writing a compiler is reliable reporting of error messages back to the user.
# This file defines some generic functionality for dealing with errors throughout the compiler project. 
#

import sys
import logging

from functools import partial
from contextlib import contextmanager

from uC_parser import UCParser

###########################################################
## uC Compiler ############################################
###########################################################

_subscribers = []
_num_errors = 0

def error(lineno, message, filename=None):
    ''' Report a compiler error to all subscribers. '''
    global _num_errors
    if not filename:
        errmsg = "{}: {}".format(lineno, message)
    else:
        errmsg = "{}:{}: {}".format(filename,lineno,message)
    for subscriber in _subscribers:
        subscriber(errmsg)
    _num_errors += 1

# NOTE The utility function `errors_reported()` returns the total number of errors reported so far.
#      Different stages of the compiler might use this to decide whether or not to keep processing or not.
#      Use `clear_errors()` to clear the total number of errors.

def errors_reported():
    ''' Return the number of errors reported. '''
    return _num_errors

def clear_errors():
    ''' Reset the total number of errors reported to 0. '''
    global _num_errors
    _num_errors = 0

# NOTE Error handling is based on a subscription based model using context-managers and the `subscribe_errors()` function. 
#     
#      For example, to route error messages to standard output, use this:
#        with subscribe_errors(print):
#            run_compiler()
#      
#      To send messages to standard error, you can do this:
#        with subscribe_errors(functools.partial(print, file=sys.stderr)):
#             run_compiler()
#
#      To route messages to a logger, you can do this:
#        log = logging.getLogger("somelogger")
#        with subscribe_errors(log.error):
#             run_compiler()
#
#      To collect error messages for the purpose of unit testing, do this:
#        errs = []
#        with subscribe_errors(errs.append):
#             run_compiler()
#        # Check errs for specific errors

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


class Compiler:
    ''' This object encapsulates the compiler and serves as a facade interface for the compiler itself. '''

    def __init__(self):
        self.total_errors = 0
        self.total_warnings = 0

    def _parse(self, ast_file, debug):
        ''' Parses the source code.\n
            If `ast_file` is not `None`, prints out the abstract syntax tree (AST).
        '''
        self.parser = UCParser()
        self.ast = self.parser.parse(self.code, '', debug)
        if ast_file is not None:
            self.ast.show(buf=ast_file, showcoord=True)

    def _do_compile(self, ast_file, debug):
        ''' Compiles the code to the given file object. '''
        self._parse(ast_file, debug)

    def compile(self, code, ast_file, debug):
        ''' Compiles the given code string. '''
        self.code = code
        with subscribe_errors(lambda msg: sys.stdout.write(msg + "\n")):
            self._do_compile(ast_file, debug)
            if not errors_reported():
                print("Compile successful.")
            else:
                print("{} error(s) encountered.".format(errors_reported()))
        return 0


def run_compiler():
    ''' Runs the command-line compiler. '''

    if len(sys.argv) < 2:
        print("Usage: ./uC.py <source-file> [-no-ast] [-debug]")
        sys.exit(1)

    emit_ast = True
    debug = False

    params = sys.argv[1:]
    files = sys.argv[1:]

    for param in params:
        if param[0] == '-':
            if param == '-no-ast':
                emit_ast = False
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
        if emit_ast:
            ast_filename = source_filename[:-3] + '.ast'
            print("Outputting the AST to %s." % ast_filename)
            ast_file = open(ast_filename, 'w')
            open_files.append(ast_file)

        source = open(source_filename, 'r')
        code = source.read()
        source.close()

        retval = Compiler().compile(code, ast_file, debug)
        for f in open_files:
            f.close()
        if retval != 0:
            sys.exit(retval)

    sys.exit(retval)


if __name__ == '__main__':
    run_compiler()