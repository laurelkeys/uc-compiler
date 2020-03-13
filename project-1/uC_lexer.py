import re
import ply.lex as lex

from ply.lex import LexToken

# NOTE For simple tokens, the regular expression can be specified as strings,
#      with the name following 't_' matching exactly one of the names supplied in `tokens`.
#      When a function is used, the regular expression rule is specified in the function documentation string.
#      The function takes a single argument of type LexToken, with attributes t.type, t.value, t.lineno, and t.lexpos.
#      The @TOKEN or @Token decorators can also be used for more complex regular expression rules, defined as variables.

# NOTE Patterns are compiled using the re.VERBOSE flag which can be used to help readability.
#      However, be aware that unescaped whitespace is ignored and comments are allowed in this mode.
#      If your pattern involves whitespace, make sure you use \s. If you need to match the # character, use [#].

# NOTE When building the master regular expression, rules are added in the following order:
#      1. All tokens defined by functions are added in the same order as they appear in the lexer file.
#      2. Tokens defined by strings are added next, by sorting them in order of decreasing regular expression length
#         (longer expressions are added first).

# NOTE expected/reserved variables:
#      - `tokens`, a list that defines all possible token names that can be produced by the lexer
#      - `t_ignore`, special rule reserved for characters that should be completely ignored in the input stream
#                    obs.: you can include the prefix "ignore_" in a token declaration to force the token to be ignored
#      - `literals`, list of literal characters, i.e. single characters that are returned "as is" when encountered by the lexer
#                    obs.: literals are checked after all of the defined regular expression rules
#      - `t_error()`, function used to handle lexing errors that occur when illegal characters are detected
#      - `t_eof()`, function used to handle an end-of-file (EOF) condition in the input

# NOTE To build the lexer, the function lex.lex() is used.
#      This function uses Python reflection to read the regular expression rules out of the calling context and build the lexer.
#      Once the lexer has been built, two methods can be used to control the lexer:
#       - lexer.input(data), Reset the lexer and store a new input string.
#       - lexer.token(), Return the next token (LexToken instance on success or None if the end of the input text is reached).

###########################################################
## uC Lexer ###############################################
###########################################################

class UCLexer():
    """ A lexer for the uC programming language.
        After building it, set the input text with `input()`, and call `token()` to get new tokens.
    """

    def __init__(self, error_func):
        """ Creates a new Lexer.\n
            `error_func` will be called in case of an error during lexing, with an error message, line and column as arguments.
        """
        self.filename = ''
        self.error_func = error_func
        self.last_token = None # last token returned from self.token()

    def build(self, **kwargs):
        """ Builds the lexer. Must be called after the lexer object is created.\n
            This method exists separately because the PLY manual warns against calling `lex.lex` inside `__init__`.
        """
        self.lexer = lex.lex(object=self, **kwargs)

    def input(self, text):
        self.lexer.input(text)

    def token(self):
        self.last_token = self.lexer.token()
        return self.last_token

    # Internal auxiliary methods
    def _find_tok_column(self, token):
        """ Find the column of the token in its line. """
        last_cr = self.lexer.lexdata.rfind('\n', 0, token.lexpos)
        return token.lexpos - last_cr

    def _make_tok_location(self, token):
        """ Returns the token's location as a tuple `(line, column)`. """
        return token.lineno, self._find_tok_column(token)

    def _reset_lineno(self):
        """ Resets the internal line number counter of the lexer to 1. """
        self.lexer.lineno = 1

    def _error(self, msg, token):
        line, column = self._make_tok_location(token)
        self.error_func(msg, line, column)
        self.lexer.skip(1)

    # Scanner (used only for testing)
    def scan(self, data, print_tokens=True):
        tokens = []
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            tokens.append(tok)
            if print_tokens:
                print(tok)
        return tokens

    # Reserved keywords
    keywords = (
        'IF', 'ELSE',
        'FOR', 'WHILE',
        'BREAK', 'RETURN',
        'ASSERT', 'PRINT', 'READ',
        'VOID', 'CHAR', 'INT', 'FLOAT', # type specifiers
    )

    keyword_map = {}
    for keyword in keywords:
        keyword_map[keyword.lower()] = keyword

    # FIXME should we include '.' as a token? (i.e. element selection by reference)
    # Token list
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
    def t_newline(self, t):
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
    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        t.type = self.keyword_map.get(t.value, 'ID')
        return t

    # Constants
    def t_INT_CONST(self, t):
        r'0|([1-9][0-9]*)'
        t.value = int(t.value)
        return t

    def t_FLOAT_CONST(self, t):
        r'((0|([1-9][0-9]*))\.[0-9]*)|((|0|([1-9][0-9]*))\.[0-9]+)'
        t.value = float(t.value)
        return t

    # FIXME is r'".*"' enough?
    t_STRING_CONST = r'\"([^\\\n]|(\\.))*?\"'

    # FIXME is r'\'.?\'' enough?
    t_CHAR_CONST = r'\'([^\\\n]|(\\.))*?\'' # FIXME should we use a function to check length is 1?

    # Comments
    def t_comment(self, t):
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count('\n')

    # Error (NOTE keep it as the last defined t_ function)
    def t_error(self, t):
        msg = "Illegal character '%s'" % repr(t.value[0])
        self._error(msg, t)
