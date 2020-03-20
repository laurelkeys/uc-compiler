

###########################################################
## uC Abstract Syntax Tree ################################
###########################################################

class Node:
    ''' Base class example for the AST nodes.\n
        Each node is expected to define the `_fields` attribute which lists the names of stored attributes.\n
        The `__init__()` method below takes positional arguments and assigns them to the appropriate fields.\n
        Any additional arguments specified as keywords are also assigned.
    '''
    _fields = []

    def __init__(self, *args, **kwargs):
        assert len(args) == len(self._fields)

        for name, value in zip(self._fields,args):
            setattr(self, name, value)

        for name, value in kwargs.items():
            setattr(self, name, value) # assign additional keyword arguments (if supplied)


class Program(Node):
    ''' This is the top of the AST, representing a uC program (a translation unit in K&R jargon).\n
        It contains a list of global-declaration's, which are either declarations (Decl), or function definitions (FuncDef).
    '''
    _fields = ['decls']


class BinaryOp(Node):
    _fields = ['lvalue', 'op', 'rvalue']


# TODO implement:
# [ ] ArrayDecl
# [ ] ArrayRef
# [ ] Assert
# [ ] Assignment
# [x] BinaryOp
# [ ] Break
# [ ] Cast
# [ ] Compound
# [ ] Constant
# [ ] Decl
# [ ] DeclList
# [ ] EmptyStatement
# [ ] ExprList
# [ ] For
# [ ] FuncCall
# [ ] FuncDecl
# [ ] FuncDef
# [ ] GlobalDecl
# [x] ID
# [ ] If
# [ ] InitList
# [ ] ParamList
# [ ] Print
# [x] Program
# [ ] PtrDecl
# [ ] Read
# [ ] Return
# [ ] Type
# [ ] VarDecl
# [ ] UnaryOp
# [ ] While