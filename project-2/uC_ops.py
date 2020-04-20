
###########################################################
## uC Operators ###########################################
###########################################################

# unary operators: +, -, ++, --, &, *, !
unary = {
    'PLUS': '+',
    'MINUS': '-',

    # prefix increment and decrement
    'PLUSPLUS': '++',
    'MINUSMINUS': '--',

    # suffix/postfix increment and decrement
    'pPLUSPLUS': 'p++',
    'pMINUSMINUS': 'p--',

    # address-of and indirection
    'ADDRESS': '&',
    'TIMES': '*',

    'NOT': '!',
}

# binary operators: +, -, *, /, %, &&, ||
binary = {

    # additive operators
    'PLUS': '+',
    'MINUS': '-',

    # multiplicative operators
    'TIMES': '*',
    'DIV': '/',
    'MOD': '%',

    # logical operators
    'AND': '&&',
    'OR': '||',
}

# relational operators: ==, !=, <, >, <=, >=
rel = {
    'EQ': '==',
    'NEQ': '!=',

    'LT': '<',
    'GT': '>',
    'LEQ': '<=',
    'GEQ': '>=',
}

# assignment operators: =, +=, -=, *=, /=, %=
assign = {
    'EQUALS': '=',

    'PLUSEQUALS': '+=',
    'MINUSEQUALS': '-=',

    'TIMESEQUALS': '*=',
    'DIVEQUALS': '/=',
    'MODEQUALS': '%=',
}
