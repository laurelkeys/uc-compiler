import uC_ops

###########################################################
## uC Built-in Types ######################################
###########################################################

class uCType:
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

    def __str__(self):
        return '{' + self.typename + '}'

    def __repr__(self):
        return '{' + self.typename + '}'


__IntType = uCType(
    'int',
    default     =   0,
    unary_ops   =   { '+', '-', '++', '--', 'p++', 'p--', '&', '*' },
    binary_ops  =   { '+', '-', '*', '/', '%' },
    rel_ops     =   { '==', '!=', '<', '>', '<=', '>=' },
    assign_ops  =   { '=', '+=', '-=', '*=', '/=', '%=' },
)

__FloatType = uCType(
    'float',
    default     =   0.0,
    unary_ops   =   { '+', '-', '++', '--', 'p++', 'p--', '&', '*' },
    binary_ops  =   { '+', '-', '*', '/', '%' },
    rel_ops     =   { '==', '!=', '<', '>', '<=', '>=' },
    assign_ops  =   { '=', '+=', '-=', '*=', '/=', '%=' },
)

__CharType = uCType(
    'char',
    default     =   '',
    unary_ops   =   None,
    binary_ops  =   { '+', '-' },
    rel_ops     =   { '==', '!=', '<', '>', '<=', '>=' },
    assign_ops  =   { '=', '+=', '-=' },
)

__StringType = uCType(
    'string',
    default     =   "",
    unary_ops   =   None, # FIXME is { '&', '*' } valid ?
    binary_ops  =   { '+' },
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=', '+=' },
)

__BoolType = uCType(
    'bool',
    default     =   False,
    unary_ops   =   { '!' }, # FIXME is { '&', '*' } valid ?
    binary_ops  =   { '&&', '||' },
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=' },
)

__VoidType = uCType(
    'void',
    default     =   None,
    unary_ops   =   None, # FIXME is { '&', '*' } valid ?
    binary_ops  =   None,
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=' },
)

__ArrayType = uCType(
    'array',
    default     =   [],
    unary_ops   =   { '&', '*' },
    binary_ops  =   None,
    rel_ops     =   { '==', '!=' },
    assign_ops  =   { '=' },
)

# Singletons
int_type    = __IntType()
float_type  = __FloatType()
char_type   = __CharType()
string_type = __StringType()
bool_type   = __BoolType()
void_type   = __VoidType()
array_type  = __ArrayType()

# TODO do we need something like a function_type, pointer_type / reference_type, etc.?
