import sys

###########################################################
## uC Abstract Syntax Tree ################################
###########################################################

class Node:
    ''' Abstract base class for the AST nodes. '''
    __slots__ = ()

    def __repr__(self):
        ''' Generates a representation of the current node. '''
        def _repr(obj):
            if not isinstance(obj, list):
                return repr(obj)
            return '[' + ',\n '.join(_repr(e).replace('\n', '\n ') for e in obj) + '\n]'

        result, indent, separator = '', '', ''
        len_class_name = len(self.__class__.__name__)
        for name in self.__slots__[:-3]: # skip coord, attrs and __weakref__
            result += separator + indent + name + '=' + (
                _repr(getattr(self, name)).replace('\n', '\n  ' + (' ' * (len(name) + len_class_name)))
            )
            indent = ' ' * len_class_name
            separator = ','
        return self.__class__.__name__ + '(' + result + indent + ')'

    def children(self):
        ''' A sequence of all children that are `Node`s. '''
        pass

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

class NodeVisitor:
    ''' Abstract base class for visiting the AST nodes.\n
        Define a `visit_<>` method for each class named `<>` you want to visit.\n
        Notes:\n
        - `generic_visit()` will be called for AST nodes for which no `visit_<>` method was defined.
        - The children of nodes for which a `visit_<>` was defined will not be visited.
          If you need this, call `generic_visit()` on the node.
    '''

    _method_cache = None

    def visit(self, node):
        ''' Visit a node. '''

        if self._method_cache is None:
            self._method_cache = {}

        print(f"v.. {node.__class__.__name__}") # FIXME remove

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

# NOTE attrs is a dictionary used to store additional information
#      (attributes) during semantic analysis, to provide context-
#      sensitive information for easier code generation

class ArrayDecl(Node):
    __slots__ = ('type', 'dim', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, type, dim, coord=None, attrs=None):
        self.type = type
        self.dim = dim
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(('type', self.type))
        if self.dim is not None: nodelist.append(('dim', self.dim))
        return tuple(nodelist)

    def __iter__(self):
        if self.type is not None:
            yield self.type
        if self.dim is not None:
            yield self.dim


class ArrayRef(Node):
    __slots__ = ('name', 'subscript', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, name, subscript, coord=None, attrs=None):
        self.name = name
        self.subscript = subscript
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.name is not None: nodelist.append(('name', self.name))
        if self.subscript is not None: nodelist.append(('subscript', self.subscript))
        return tuple(nodelist)

    def __iter__(self):
        if self.name is not None:
            yield self.name
        if self.subscript is not None:
            yield self.subscript


class Assert(Node):
    __slots__ = ('expr', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, expr, coord=None, attrs=None):
        self.expr = expr
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    def __iter__(self):
        if self.expr is not None:
            yield self.expr


class Assignment(Node):
    __slots__ = ('op', 'lvalue', 'rvalue', 'coord', 'attrs', '__weakref__')

    attr_names = ('op', )

    def __init__(self, op, lvalue, rvalue, coord=None, attrs=None):
        self.op = op
        self.lvalue = lvalue
        self.rvalue = rvalue
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.lvalue is not None: nodelist.append(('lvalue', self.lvalue))
        if self.rvalue is not None: nodelist.append(('rvalue', self.rvalue))
        return tuple(nodelist)

    def __iter__(self):
        if self.lvalue is not None:
            yield self.lvalue
        if self.rvalue is not None:
            yield self.rvalue


class BinaryOp(Node):
    __slots__ = ('op', 'left', 'right', 'coord', 'attrs', '__weakref__')

    attr_names = ('op', )

    def __init__(self, op, left, right, coord=None, attrs=None):
        self.op = op
        self.left = left
        self.right = right
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.left is not None: nodelist.append(('left', self.left))
        if self.right is not None: nodelist.append(('right', self.right))
        return tuple(nodelist)

    def __iter__(self):
        if self.left is not None:
            yield self.left
        if self.right is not None:
            yield self.right


class Break(Node):
    __slots__ = ('coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, coord=None, attrs=None):
        self.coord = coord
        self.attrs = {}

    def children(self):
        return ()

    def __iter__(self):
        return
        yield


class Cast(Node):
    __slots__ = ('type', 'expr', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, type, expr, coord=None, attrs=None):
        self.type = type
        self.expr = expr
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(('type', self.type))
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    def __iter__(self):
        if self.type is not None:
            yield self.type
        if self.expr is not None:
            yield self.expr


class Compound(Node):
    __slots__ = ('decls', 'stmts', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, decls, stmts, coord=None, attrs=None):
        self.decls = decls
        self.stmts = stmts
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        for i, child in enumerate(self.decls or []):
            nodelist.append(('decls%d]' % i, child))
        for i, child in enumerate(self.stmts or []):
            nodelist.append(('stmts%d]' % i, child))
        return tuple(nodelist)

    def __iter__(self):
        for child in (self.decls or []):
            yield child
        for child in (self.stmts or []):
            yield child


class Constant(Node):
    __slots__ = ('type', 'value', 'coord', 'attrs', '__weakref__')

    attr_names = ('type', 'value', )

    def __init__(self, type, value, coord=None, attrs=None):
        self.type = type
        self.value = value
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def __iter__(self):
        return
        yield


class Decl(Node):
    __slots__ = ('name', 'type', 'init', 'coord', 'attrs', '__weakref__')

    attr_names = ('name', )

    def __init__(self, name, type, init, coord=None, attrs=None):
        self.name = name
        self.type = type
        self.init = init
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(('type', self.type))
        if self.init is not None: nodelist.append(('init', self.init))
        return tuple(nodelist)

    def __iter__(self):
        if self.type is not None:
            yield self.type
        if self.init is not None:
            yield self.init


class DeclList(Node):
    __slots__ = ('decls', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, decls, coord=None, attrs=None):
        self.decls = decls
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        for i, child in enumerate(self.decls or []):
            nodelist.append(('decls%d]' % i, child))
        return tuple(nodelist)

    def __iter__(self):
        for child in (self.decls or []):
            yield child


class EmptyStatement(Node):
    __slots__ = ('coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, coord=None, attrs=None):
        self.coord = coord
        self.attrs = {}

    def children(self):
        return ()

    def __iter__(self):
        return
        yield


class ExprList(Node):
    __slots__ = ('exprs', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, exprs, coord=None, attrs=None):
        self.exprs = exprs
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        for i, child in enumerate(self.exprs or []):
            nodelist.append(('exprs%d]' % i, child))
        return tuple(nodelist)

    def __iter__(self):
        for child in (self.exprs or []):
            yield child


class For(Node):
    __slots__ = ('init', 'cond', 'next', 'body', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, init, cond, next, body, coord=None, attrs=None):
        self.init = init
        self.cond = cond
        self.next = next
        self.body = body
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.init is not None: nodelist.append(('init', self.init))
        if self.cond is not None: nodelist.append(('cond', self.cond))
        if self.next is not None: nodelist.append(('next', self.next))
        if self.body is not None: nodelist.append(('body', self.body))
        return tuple(nodelist)

    def __iter__(self):
        if self.init is not None:
            yield self.init
        if self.cond is not None:
            yield self.cond
        if self.next is not None:
            yield self.next
        if self.body is not None:
            yield self.body


class FuncCall(Node):
    __slots__ = ('name', 'args', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, name, args, coord=None, attrs=None):
        self.name = name
        self.args = args
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.name is not None: nodelist.append(('name', self.name))
        if self.args is not None: nodelist.append(('args', self.args))
        return tuple(nodelist)

    def __iter__(self):
        if self.name is not None:
            yield self.name
        if self.args is not None:
            yield self.args


class FuncDecl(Node):
    __slots__ = ('args', 'type', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, args, type, coord=None, attrs=None):
        self.args = args
        self.type = type
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.args is not None: nodelist.append(('args', self.args))
        if self.type is not None: nodelist.append(('type', self.type))
        return tuple(nodelist)

    def __iter__(self):
        if self.args is not None:
            yield self.args
        if self.type is not None:
            yield self.type


class FuncDef(Node):
    __slots__ = ('spec', 'decl', 'param_decls', 'body', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, spec, decl, param_decls, body, coord=None, attrs=None):
        self.spec = spec
        self.decl = decl
        self.param_decls = param_decls
        self.body = body
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.spec is not None: nodelist.append(('spec', self.spec))
        if self.decl is not None: nodelist.append(('decl', self.decl))
        if self.body is not None: nodelist.append(('body', self.body))
        for i, child in enumerate(self.param_decls or []):
            nodelist.append(('param_decls%d]' % i, child))
        return tuple(nodelist)

    def __iter__(self):
        if self.spec is not None:
            yield self.spec
        if self.decl is not None:
            yield self.decl
        if self.body is not None:
            yield self.body
        for child in (self.param_decls or []):
            yield child


class GlobalDecl(Node):
    __slots__ = ('decls', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, decls, coord=None, attrs=None):
        self.decls = decls
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        for i, child in enumerate(self.decls or []):
            nodelist.append(('decls%d]' % i, child))
        return tuple(nodelist)

    def __iter__(self):
        for child in (self.decls or []):
            yield child


class ID(Node):
    __slots__ = ('name', 'coord', 'attrs', '__weakref__')

    attr_names = ('name', )

    def __init__(self, name, coord=None, attrs=None):
        self.name = name
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def __iter__(self):
        return
        yield


class If(Node):
    __slots__ = ('cond', 'ifthen', 'ifelse', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, cond, ifthen, ifelse, coord=None, attrs=None):
        self.cond = cond
        self.ifthen = ifthen
        self.ifelse = ifelse
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.cond is not None: nodelist.append(('cond', self.cond))
        if self.ifthen is not None: nodelist.append(('ifthen', self.ifthen))
        if self.ifelse is not None: nodelist.append(('ifelse', self.ifelse))
        return tuple(nodelist)

    def __iter__(self):
        if self.cond is not None:
            yield self.cond
        if self.ifthen is not None:
            yield self.ifthen
        if self.ifelse is not None:
            yield self.ifelse


class InitList(Node):
    __slots__ = ('exprs', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, exprs, coord=None, attrs=None):
        self.exprs = exprs
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        for i, child in enumerate(self.exprs or []):
            nodelist.append(('exprs%d]' % i, child))
        return tuple(nodelist)

    def __iter__(self):
        for child in (self.exprs or []):
            yield child


class ParamList(Node):
    __slots__ = ('params', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, params, coord=None, attrs=None):
        self.params = params
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        for i, child in enumerate(self.params or []):
            nodelist.append(('params%d]' % i, child))
        return tuple(nodelist)

    def __iter__(self):
        for child in (self.params or []):
            yield child


class Print(Node):
    __slots__ = ('expr', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, expr, coord=None, attrs=None):
        self.expr = expr
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    def __iter__(self):
        if self.expr is not None:
            yield self.expr


class Program(Node):
    ''' This is the top of the AST, representing a uC program.\n
        It contains a list of <global_declaration>'s, which are either 
        declarations (`Decl` wrapped by `GlobalDecl`), or function definitions (`FuncDef`).
    '''
    __slots__ = ('gdecls', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, gdecls, coord=None, attrs=None):
        self.gdecls = gdecls
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        for i, child in enumerate(self.gdecls or []):
            nodelist.append(('gdecls%d]' % i, child))
        return tuple(nodelist)

    def __iter__(self):
        for child in (self.gdecls or []):
            yield child


class PtrDecl(Node):
    __slots__ = ('type', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, type, coord=None, attrs=None):
        self.type = type
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(('type', self.type))
        return tuple(nodelist)

    def __iter__(self):
        if self.type is not None:
            yield self.type


class Read(Node):
    __slots__ = ('expr', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, expr, coord=None, attrs=None):
        self.expr = expr
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    def __iter__(self):
        if self.expr is not None:
            yield self.expr


class Return(Node):
    __slots__ = ('expr', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, expr, coord=None, attrs=None):
        self.expr = expr
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    def __iter__(self):
        if self.expr is not None:
            yield self.expr


class Type(Node):
    __slots__ = ('names', 'coord', 'attrs', '__weakref__')

    attr_names = ('names', )

    def __init__(self, names, coord=None, attrs=None):
        self.names = names
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def __iter__(self):
        return
        yield


class VarDecl(Node):
    __slots__ = ('declname', 'type', 'coord', 'attrs', '__weakref__')

    attr_names = () # NOTE don't print declname

    def __init__(self, declname, type, coord=None, attrs=None):
        self.declname = declname
        self.type = type
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(('type', self.type))
        return tuple(nodelist)

    def __iter__(self):
        if self.type is not None:
            yield self.type


class UnaryOp(Node):
    __slots__ = ('op', 'expr', 'coord', 'attrs', '__weakref__')

    attr_names = ('op', )

    def __init__(self, op, expr, coord=None, attrs=None):
        self.op = op
        self.expr = expr
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    def __iter__(self):
        if self.expr is not None:
            yield self.expr


class While(Node):
    __slots__ = ('cond', 'body', 'coord', 'attrs', '__weakref__')

    attr_names = ()

    def __init__(self, cond, body, coord=None, attrs=None):
        self.cond = cond
        self.body = body
        self.coord = coord
        self.attrs = {}

    def children(self):
        nodelist = []
        if self.cond is not None: nodelist.append(('cond', self.cond))
        if self.body is not None: nodelist.append(('body', self.body))
        return tuple(nodelist)

    def __iter__(self):
        if self.cond is not None:
            yield self.cond
        if self.body is not None:
            yield self.body
