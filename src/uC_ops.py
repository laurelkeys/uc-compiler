
###########################################################
## uC Operators ###########################################
###########################################################

# unary operators: +, -, ++, --, &, *, !
unary_ops = {
    '+': 'PLUS',
    '-': 'MINUS',

    # prefix increment and decrement
    '++': 'PLUSPLUS',
    '--': 'MINUSMINUS',

    # suffix/postfix increment and decrement
    'p++': 'pPLUSPLUS',
    'p--': 'pMINUSMINUS',

    # address-of and indirection
    '&': 'ADDRESS',
    '*': 'TIMES',

    '!': 'NOT',
}

# binary operators: +, -, *, /, %, &&, ||
binary_ops = {

    # additive operators
    '+': 'PLUS',
    '-': 'MINUS',

    # multiplicative operators
    '*': 'TIMES',
    '/': 'DIV',
    '%': 'MOD',

    # logical operators
    '&&': 'AND',
    '||': 'OR',
}

# relational operators: ==, !=, <, >, <=, >=
rel_ops = {
    '==': 'EQ',
    '!=': 'NEQ',

    '<': 'LT',
    '>': 'GT',
    '<=': 'LEQ',
    '>=': 'GEQ',
}

# assignment operators: =, +=, -=, *=, /=, %=
assign_ops = {
    '=': 'EQUALS',

    '+=': 'PLUSEQUALS',
    '-=': 'MINUSEQUALS',

    '*=': 'TIMESEQUALS',
    '/=': 'DIVEQUALS',
    '%=': 'MODEQUALS',
}


if __name__ == "__main__":
    print("unary operators:", ', '.join(unary_ops))
    print("binary operators:", ', '.join(binary_ops))
    print("relational operators:", ', '.join(rel_ops))
    print("assignment operators:", ', '.join(assign_ops))
