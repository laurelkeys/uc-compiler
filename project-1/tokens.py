[
    # identifiers
    'ID',

    # constants
    'INT_CONST', 'FLOAT_CONST',
    'CHAR_CONST', 'STRING_CONST',  # FIXME check reference name, and whether or not
                                   #       single chars will be treated differently from strings

    # reserved keywords: if, else, for, while, break, return, assert, print, read, void, char, int, float
    'IF', 'ELSE',
    'FOR', 'WHILE',
    'BREAK', 'RETURN',
    'ASSERT', 'PRINT', 'READ',
    'VOID', 'CHAR', 'INT', 'FLOAT',  # type specifiers

    # braces, brackets and parenthesis
    ('LBRACE', '{'),
    ('RBRACE', '}'),
    ('LBRACKET', '['),
    ('RBRACKET', ']'),
    ('LPAREN', '('),
    ('RPAREN', ')'),

    # comma and semicolon
    ('COMMA', ','),
    ('SEMI', ';'),

    # binary operators: *, /, %, +, -, <, <=, >, >=, ==, !=, &&, ||
    ('TIMES', '*'),
    ('DIV', '/'),   # FIXME check reference name
    ('MOD', '%'),   # FIXME check reference name
    ('PLUS', '+'),
    ('MINUS', '-'),
    ('LT', '<'),
    ('LEQ', '<='),  # FIXME check reference name
    ('GT', '>'),
    ('GEQ', '>='),  # FIXME check reference name
    ('EQ', '=='),
    ('NEQ', '=='),  # FIXME check reference name
    ('AND', '&&'),  # FIXME check reference name
    ('OR', '||'),   # FIXME check reference name

    # unary operators: ++, --, &, *, +, -, !
    ('PLUSPLUS', '++'),
    ('MINUSMINUS', '--'),  # FIXME check reference name
    ('ADDRESS', '&'),
    ('NOT', '!'),          # FIXME check reference name
    # FIXME should there be a token for unary *, +, - ?

    # assignment operators: =, *=, /=, %=, +=, -=
    ('EQUALS', '='),
    ('TIMESEQUALS', '*='),  # FIXME check reference name
    ('DIVEQUALS', '/='),    # FIXME check reference name
    ('MODEQUALS', '%='),    # FIXME check reference name
    ('PLUSEQUALS', '+='),   # FIXME check reference name
    ('MINUSEQUALS', '-='),  # FIXME check reference name
]