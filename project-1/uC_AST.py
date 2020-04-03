import sys

###########################################################
## uC Abstract Syntax Tree ################################
###########################################################

class Node:
    ''' Abstract base class for the AST nodes.\n
        Each node is expected to define the `_fields` attribute which lists the names of stored attributes.\n
        The `__init__()` method below takes positional arguments and assigns them to the appropriate fields.\n
        Any additional arguments specified as keywords are also assigned.
    '''
    _fields = []
    attr_names = ()

    def __init__(self, *args, **kwargs):
        assert len(args) == len(self._fields)

        for name, value in zip(self._fields, args):
            setattr(self, name, value)

        for name, value in kwargs.items():
            setattr(self, name, value) # assign additional keyword arguments (if supplied)

    def __repr__(self):
        def _repr(obj):
            if not isinstance(obj, list):
                return repr(obj)
            return '[' + ',\n '.join(_repr(e).replace('\n', '\n ') for e in obj) + '\n]'

        result, indent, separator = '', '', ''
        len_class_name = len(self.__class__.__name__)
        for name in self.__dict__.keys(): # FIXME __slots__[:-2]:
            result += separator + indent + name + '=' + (
                _repr(getattr(self, name)).replace('\n', '\n  ' + (' ' * (len(name) + len_class_name)))
            )
            indent = ' ' * len_class_name
            separator = ','
        return self.__class__.__name__ + '(' + result + indent + ')'

    def children(self):
        ''' A sequence of all children that are `Node`s. '''
        return [] # FIXME pass

    def show(self, buf=sys.stdout, offset=0, attrnames=False, nodenames=False, showcoord=False, _my_node_name=None):
        ''' Pretty print the Node and all its attributes and children (recursively) to a buffer, where:
            - `buf`: Open IO buffer into which the Node is printed.
            - `offset`: Initial offset (amount of leading spaces).
            - `attrnames`: True if you want to see the attribute names in name=value pairs. False to only see the values.
            - `nodenames`: True if you want to see the actual node names within their parents.
            - `showcoord`: True if you want the coordinates of each Node to be displayed.
        '''
        lead = ' ' * offset
        if nodenames and _my_node_name is not None:
            buf.write(lead + self.__class__.__name__+ ' <' + _my_node_name + '>: ')
        else:
            buf.write(lead + self.__class__.__name__+ ': ')

        if self.attr_names:
            if attrnames:
                nvlist = [(n, getattr(self, n)) for n in self.attr_names if getattr(self, n) is not None]
                attrstr = ', '.join('%s=%s' % nv for nv in nvlist)
            else:
                vlist = [getattr(self, n) for n in self.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            buf.write(attrstr)

        if showcoord:
            if self.coord:
                buf.write('%s' % self.coord)
        buf.write('\n')

        for (child_name, child) in self.children():
            child.show(buf, offset + 4, attrnames, nodenames, showcoord, child_name)

class NodeVisitor(object):
    ''' Abstract base class for visiting the AST nodes.\n
        Define a `visit_<>` method for each class named `<>` you want to visit.\n
        Notes:\n
        - `generic_visit()` will be called for AST nodes for which no `visit_<>` method was defined
        - The children of nodes for which a `visit_<> was defined will not be visited.
          If you need this, call `generic_visit()` on the node.
    '''

    _method_cache = None

    def visit(self, node):
        ''' Visit a node. '''

        if self._method_cache is None:
            self._method_cache = {}

        visitor = self._method_cache.get(node.__class__.__name__, None)
        if visitor is None:
            method = 'visit_' + node.__class__.__name__
            visitor = getattr(self, method, self.generic_visit)
            self._method_cache[node.__class__.__name__] = visitor

        return visitor(node)

    def generic_visit(self, node):
        ''' Called if no explicit visitor function exists for a node.\n
            Implements preorder visiting of the node.
        '''
        for c in node:
            self.visit(c)

###########################################################
## uC Nodes ###############################################
###########################################################

class ArrayDecl(Node):
    _fields = ['type', 'dim']

class ArrayRef(Node):
    _fields = ['name', 'subscript']

class Assert(Node):
    _fields = ['expr']

class Assignment(Node):
    _fields = ['op', 'lvalue', 'rvalue']
    attr_names = ('op', )

class BinaryOp(Node):
    _fields = ['op', 'left', 'right']
    attr_names = ('op', )

class Break(Node):
    _fields = []

class Cast(Node):
    _fields = ['type', 'expr']

class Compound(Node):
    _fields = ['decls', 'stmts']

class Constant(Node):
    _fields = ['type', 'value']
    attr_names = ('type', 'value', )

class Decl(Node):
    _fields = ['name', 'type', 'init']
    attr_names = ('name', )

class DeclList(Node):
    _fields = ['decls']

class EmptyStatement(Node):
    _fields = []

class ExprList(Node):
    _fields = ['exprs']

class For(Node):
    _fields = ['init', 'cond', 'next', 'body']

class FuncCall(Node):
    _fields = ['name', 'args']

class FuncDecl(Node):
    _fields = ['args', 'type']

class FuncDef(Node):
    _fields = ['decl', 'param_decls', 'body']

class GlobalDecl(Node): # FIXME
    _fields = ['gdecl']

class ID(Node):
    _fields = ['name']
    attr_names = ('name', )

class If(Node):
    _fields = ['cond', 'ifthen', 'ifelse']

class InitList(Node):
    _fields = ['exprs']

class ParamList(Node):
    _fields = ['params']

class Print(Node):
    _fields = ['expr']

class Program(Node): # FIXME
    ''' This is the top of the AST, representing a uC program (a translation unit in K&R jargon).\n
        It contains a list of <global_declaration>'s, which are either declarations (Decl), or function definitions (FuncDef).
    '''
    _fields = ['gdecls']

class PtrDecl(Node):
    _fields = ['type']

class Read(Node):
    _fields = ['expr']

class Return(Node):
    _fields = ['expr']

class Type(Node):
    _fields = ['names']
    attr_names = ('names', )

class VarDecl(Node):
    _fields = ['declname', 'type']
    attr_names = ('declname', ) # TODO don't print this

class UnaryOp(Node):
    _fields = ['op', 'expr']
    attr_names = ('op', )

class While(Node):
    _fields = ['cond', 'body']
