import uC_ops

###########################################################
## uC Built-in Types ######################################
###########################################################

class UCType:
    ''' Class that represents a type in the uC language.\n
        Types are declared as singleton instances of this type.
    '''

    def __init__(self, typename, default, unary_ops=None, binary_ops=None, rel_ops=None, assign_ops=None):
        self.typename = typename
        self.default = default

        self.unary_ops = unary_ops or set()
        self.binary_ops = binary_ops or set()
        self.rel_ops = rel_ops or set()
        self.assign_ops = assign_ops or set()

        assert all(op in uC_ops.unary_ops.values() for op in self.unary_ops)
        assert all(op in uC_ops.binary_ops.values() for op in self.binary_ops)
        assert all(op in uC_ops.rel_ops.values() for op in self.rel_ops)
        assert all(op in uC_ops.assign_ops.values() for op in self.assign_ops)

    def __eq__(self, other):
        if isinstance(other, UCType):
            return other.typename == self.typename
        return False

    def __str__(self):
        return '{' + self.typename + '}'

    def __repr__(self):
        return '{' + self.typename + '}'


TYPE_INT = uCType(
    'int',
    default     =   0,
    unary_ops   =   { '+', '-', '++', '--', 'p++', 'p--', '&', '*' },
    binary_ops  =   { '+', '-', '*', '/', '%' },
    rel_ops     =   { '==', '!=', '<', '>', '<=', '>=' },
    assign_ops  =   { '=', '+=', '-=', '*=', '/=', '%=' },
)

TYPE_FLOAT = uCType(
    'float',
    default     =   0.0,
    unary_ops   =   { '+', '-', '++', '--', 'p++', 'p--', '&', '*' },
    binary_ops  =   { '+', '-', '*', '/', '%' },
    rel_ops     =   { '==', '!=', '<', '>', '<=', '>=' },
    assign_ops  =   { '=', '+=', '-=', '*=', '/=', '%=' },
)

TYPE_CHAR = uCType(
    'char',
    default     =   '',
    unary_ops   =   None,
    binary_ops  =   { '+', '-' },
    rel_ops     =   { '==', '!=', '<', '>', '<=', '>=' },
    assign_ops  =   { '=', '+=', '-=' },
)

TYPE_STRING = uCType(
    'string',
    default     =   "",
    unary_ops   =   None, # FIXME is { '&', '*' } valid ?
    binary_ops  =   { '+' },
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=', '+=' },
)

TYPE_BOOL = uCType(
    'bool',
    default     =   False,
    unary_ops   =   { '!' }, # FIXME is { '&', '*' } valid ?
    binary_ops  =   { '&&', '||' },
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=' },
)

TYPE_VOID = uCType(
    'void',
    default     =   None,
    unary_ops   =   None, # FIXME is { '&', '*' } valid ?
    binary_ops  =   None,
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=' },
)

TYPE_ARRAY = uCType(
    'array',
    default     =   [],
    unary_ops   =   { '&', '*' },
    binary_ops  =   None,
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=' },
)

# TODO implement for pointers / references
# TYPE_PTR = uCType(
#     'ptr',
#     default     =   None, # 0
#     unary_ops   =   { '&', '*' }, # '++', '--', 'p++', 'p--',
#     binary_ops  =   None, # '+', '-',
#     rel_ops     =   { '==', '!=' }, # '<', '>', '<=', '>='
#     assign_ops  =   { '=' }, # '+=', '-='
# )

