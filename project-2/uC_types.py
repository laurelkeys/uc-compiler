import uC_ops

###########################################################
## uC Built-in Types ######################################
###########################################################

class uCType(object):
    ''' Class that represents a type in the uC language.\n
        Types are declared as singleton instances of this type.
    '''

    def __init__(self, typename, unary_ops=None, binary_ops=None, rel_ops=None, assign_ops=None):
        self.typename = typename
        assert (
            all(op in uC_ops.unary for op in unary_ops)
            and all(op in uC_ops.binary for op in binary_ops)
            and all(op in uC_ops.rel for op in rel_ops)
            and all(op in uC_ops.assign for op in assign_ops)
        )
        self.unary_ops = unary_ops or set()
        self.binary_ops = binary_ops or set()
        self.rel_ops = rel_ops or set()
        self.assign_ops = assign_ops or set()

IntType = uCType("int",
    unary_ops   = {"+", "-", "++", "--", "p++", "p--", "&", "*"},
    binary_ops  = {"+", "-", "*", "/", "%"},
    rel_ops     = {"==", "!=", "<", ">", "<=", ">="},
    assign_ops  = {"=", "+=", "-=", "*=", "/=", "%="},
)

FloatType = uCType("float",
    unary_ops   = {"+", "-", "++", "--", "p++", "p--", "&", "*"},
    binary_ops  = {"+", "-", "*", "/", "%"},
    rel_ops     = {"==", "!=", "<", ">", "<=", ">="},
    assign_ops  = {"=", "+=", "-=", "*=", "/=", "%="},
)

CharType = uCType("char",
    unary_ops   = None,
    binary_ops  = {"+", "-"},
    rel_ops     = {"==", "!=", "<", ">", "<=", ">="},
    assign_ops  = {"=", "+=", "-="},
)

StringType = uCType("string",
    unary_ops   = None,
    binary_ops  = {"+"},
    rel_ops     = {"==", "!="},
    assign_ops  = {"=", "+="},
)

ArrayType = uCType("array",
    unary_ops   = {"&", "*"},
    binary_ops  = None,
    rel_ops     = {"==", "!="},
    assign_ops  = {"="},
)

# TODO bool, etc.
