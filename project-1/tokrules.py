
keywords = (
    'IF', 'ELSE',
    'FOR', 'WHILE',
    'BREAK', 'RETURN',
    'ASSERT', 'PRINT', 'READ',
    'VOID', 'CHAR', 'INT', 'FLOAT', # type specifiers
)

# FIXME should we include '.' as a token? (i.e. element selection by reference)
tokens = (
    # identifiers
    'ID',

    # constants
    'INT_CONST', 'FLOAT_CONST',
    'CHAR_CONST', 'STRING_CONST',

    # braces, brackets and parenthesis
    'LBRACE', 'RBRACE',
    'LBRACKET', 'RBRACKET',
    'LPAREN', 'RPAREN',

    # comma and semicolon
    'COMMA',
    'SEMI',

    # assignment operators: =, *=, /=, %=, +=, -=
    'EQUALS',
    'TIMESEQUALS', 'DIVEQUALS',
    'MODEQUALS',
    'PLUSEQUALS', 'MINUSEQUALS',

    # binary operators: *, /, %, +, -, <, <=, >, >=, ==, !=, &&, ||
    'TIMES', 'DIV',
    'MOD',
    'PLUS', 'MINUS',
    'LT', 'LEQ', 'GT', 'GEQ', 'EQ', 'NEQ',
    'AND', 'OR',

    # unary operators: ++, --, +, -, &, *, !
    'PLUSPLUS', 'MINUSMINUS',
    'UPLUS', 'UMINUS',
    'ADDRESS', 'UTIMES',
    'NOT',

    # reserved keywords
) + keywords

# Completely ignored characters
t_ignore = ' \t'

# Newlines
def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count('\n')

# Delimiters
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'

t_COMMA = r','
t_SEMI = r';'

# Assignment operators
t_EQUALS = r'='
t_TIMESEQUALS = r'\*='
t_DIVEQUALS = r'/='
t_MODEQUALS = r'%='
t_PLUSEQUALS = r'\+='
t_MINUSEQUALS = r'\-='

# Binary operators
t_TIMES = r'\*'
t_DIV = r'/'
t_MOD = r'%'
t_PLUS = r'\+'
t_MINUS = r'\-'

t_LT = r'<'
t_LEQ = r'<='
t_GT = r'>'
t_GEQ = r'>='
t_EQ = r'=='
t_NEQ = r'!='

t_AND = r'\&\&'
t_OR = r'\|\|'

# Unary operators
t_PLUSPLUS = r'\+\+'
t_MINUSMINUS = r'\-\-'
t_UPLUS = r'\+'
t_UMINUS = r'\-'

t_ADDRESS = r'\&' # address-of
t_UTIMES = r'\*'  # indirection (dereference)

t_NOT = r'!'

# Identifiers and reserved words
keyword_map = {}
for keyword in keywords:
    keyword_map[keyword.lower()] = keyword

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = keyword_map.get(t.value, default="ID")
    return t

# Constants
def t_INT_CONST(t):
    r'0|([1-9][0-9]*)'
    t.value = int(t.value)
    return t

def t_FLOAT_CONST(t):
    r'((0|([1-9][0-9]*))\.[0-9]*)|((|0|([1-9][0-9]*))\.[0-9]+)'
    t.value = float(t.value)
    return t

# FIXME is r'".*"' enough?
t_STRING_CONST = r'\"([^\\\n]|(\\.))*?\"'

# FIXME is r'\'.?\'' enough?
t_CHAR_CONST = r'\'([^\\\n]|(\\.))*?\'' # FIXME should we use a function to check length is 1?

# Comments
def t_comment(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')

# Error
# FIXME define t_error()