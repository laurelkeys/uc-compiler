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
        return self.typename

    def __repr__(self):
        return self.typename


TYPE_INT = UCType(
    'int',
    default     =   0,
    unary_ops   =   { '+', '-', '++', '--', 'p++', 'p--', '&', '*' },
    binary_ops  =   { '+', '-', '*', '/', '%' },
    rel_ops     =   { '==', '!=', '<', '>', '<=', '>=' },
    assign_ops  =   { '=', '+=', '-=', '*=', '/=', '%=' },
)

TYPE_FLOAT = UCType(
    'float',
    default     =   0.0,
    unary_ops   =   { '+', '-', '++', '--', 'p++', 'p--', '&', '*' },
    binary_ops  =   { '+', '-', '*', '/', '%' },
    rel_ops     =   { '==', '!=', '<', '>', '<=', '>=' },
    assign_ops  =   { '=', '+=', '-=', '*=', '/=', '%=' },
)

TYPE_CHAR = UCType(
    'char',
    default     =   '',
    unary_ops   =   { '&', '*' },
    binary_ops  =   { '+', '-' },
    rel_ops     =   { '==', '!=', '<', '>', '<=', '>=' },
    assign_ops  =   { '=', '+=', '-=' },
)

TYPE_STRING = UCType(
    'string',
    default     =   "",
    unary_ops   =   None,
    binary_ops  =   { '+' },
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=', '+=' },
)

TYPE_BOOL = UCType(
    'bool',
    default     =   False,
    unary_ops   =   { '!', '&', '*' },
    binary_ops  =   { '&&', '||' },
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=' },
)

TYPE_VOID = UCType(
    'void',
    default     =   None,
    unary_ops   =   { '&', '*' },
    binary_ops  =   None,
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=' },
)

TYPE_ARRAY = UCType(
    'array',
    default     =   [],
    unary_ops   =   { '&', '*' },
    binary_ops  =   None,
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=' },
)

TYPE_FUNC = UCType(
    'func',
    default     =   None,
    unary_ops   =   { '&', '*' },
    binary_ops  =   None,
    rel_ops     =   None,
    assign_ops  =   None,
)

# TODO implement for pointers / references
#TYPE_PTR = UCType(
#    'ptr',
#    default     =   0,
#    unary_ops   =   { '&', '*' },
#    binary_ops  =   None,
#    rel_ops     =   { '==', '!=' },
#    assign_ops  =   { '=' },
#)


def from_name(typename: str) -> UCType:
    # FIXME turn into a dict
    if   typename == "int":     return TYPE_INT
    elif typename == "float":   return TYPE_FLOAT
    elif typename == "char":    return TYPE_CHAR
    elif typename == "string":  return TYPE_STRING
    elif typename == "void":    return TYPE_VOID

    elif typename == "array":   return TYPE_ARRAY
    elif typename == "bool":    return TYPE_BOOL
    elif typename == "func":    return TYPE_FUNC
    #elif typename == "ptr":     return TYPE_PTR

    else: assert False, f"Unkown type name: '{typename}'"
