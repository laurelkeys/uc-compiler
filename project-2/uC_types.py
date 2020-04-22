import uC_ops

# TODO triple-check all of this (also, look for an official C reference)

###########################################################
## uC Built-in Types ######################################
###########################################################

class uCType(object):
    ''' Class that represents a type in the uC language.\n
        Types are declared as singleton instances of this type.
    '''

    def __init__(self, typename, default, unary_ops=None, binary_ops=None, rel_ops=None, assign_ops=None):
        self.typename = typename
        self.default = default
        assert (
            all(op in uC_ops.unary_ops.items() for op in unary_ops)
            and all(op in uC_ops.binary_ops.items() for op in binary_ops)
            and all(op in uC_ops.rel_ops.items() for op in rel_ops)
            and all(op in uC_ops.assign_ops.items() for op in assign_ops)
        )
        self.unary_ops = unary_ops or set()
        self.binary_ops = binary_ops or set()
        self.rel_ops = rel_ops or set()
        self.assign_ops = assign_ops or set()

    def __eq__(self, other):
        if isinstance(other, uCType):
            return other.typename == self.typename
        return False


IntType = uCType(
    'int',
    default     =   0,
    unary_ops   =   { '+', '-', '++', '--', 'p++', 'p--', '&', '*' },
    binary_ops  =   { '+', '-', '*', '/', '%' },
    rel_ops     =   { '==', '!=', '<', '>', '<=', '>=' },
    assign_ops  =   { '=', '+=', '-=', '*=', '/=', '%=' },
)

FloatType = uCType(
    'float',
    default     =   0.0,
    unary_ops   =   { '+', '-', '++', '--', 'p++', 'p--', '&', '*' },
    binary_ops  =   { '+', '-', '*', '/', '%' },
    rel_ops     =   { '==', '!=', '<', '>', '<=', '>=' },
    assign_ops  =   { '=', '+=', '-=', '*=', '/=', '%=' },
)

CharType = uCType(
    'char',
    default     =   '',
    unary_ops   =   None,
    binary_ops  =   { '+', '-' },
    rel_ops     =   { '==', '!=', '<', '>', '<=', '>=' },
    assign_ops  =   { '=', '+=', '-=' },
)

StringType = uCType(
    'string',
    default     =   "",
    unary_ops   =   None,
    binary_ops  =   { '+' },
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=', '+=' },
)

BoolType = uCType(
    'bool',
    default     =   False,
    unary_ops   =   { '!' },
    binary_ops  =   { '&&', '||' },
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=' },
)

VoidType = uCType(
    'void',
    default     =   None,
    unary_ops   =   None,
    binary_ops  =   None,
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=' },
)

ArrayType = uCType(
    'array',
    default     =   [],
    unary_ops   =   { '&', '*' },
    binary_ops  =   None,
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=' },
)


int_type    = IntType()
float_type  = FloatType()
char_type   = CharType()
string_type = StringType()
bool_type   = BoolType()
void_type   = VoidType()
array_type  = ArrayType()

# TODO do we need something like a func_type, ptr_type, etc.?
