import ply.lex as lex

from ply.lex import LexToken

###########################################################
## uC Lexer ###############################################
###########################################################

class UCLexer():
    """ A lexer for the uC programming language.
        After building it, set the input text with `input()`, and call `token()` to get new tokens.
    """

    def __init__(self, error_func):
        """ Creates a new Lexer.
            \n
            `error_func` will be called with an error message, line and column as arguments,
            in case of an error during lexing.
        """
        self.filename = ''
        self.error_func = error_func
        self.last_token = None # last token returned from self.token()

    def build(self, **kwargs):
        """ Builds the lexer from the specification.
            Must be called after the lexer object is created.
            \n
            This method exists separately because the PLY manual
            warns against calling `lex.lex` inside `__init__`.
        """
        self.lexer = lex.lex(object=self, **kwargs)

    def reset_lineno(self):
        """ Resets the internal line number counter of the lexer to 1. """
        self.lexer.lineno = 1

    def input(self, text):
        self.lexer.input(text)

    def token(self):
        self.last_token = self.lexer.token()
        return self.last_token

    def find_tok_column(self, token):
        """ Find the column of the token in its line. """
        last_cr = self.lexer.lexdata.rfind('\n', start=0, end=token.lexpos)
        return token.lexpos - last_cr

    # Internal auxiliary methods
    def _error(self, msg, token):
        line, column = self._make_tok_location(token)
        self.error_func(msg, line, column)
        self.lexer.skip(1)

    def _make_tok_location(self, token):
        return token.lineno, self.find_tok_column(token)

    # Reserved keywords
    keywords = (
        'ASSERT', 'BREAK', 'CHAR', 'ELSE', 'FLOAT', 'FOR', 'IF',
        'INT', 'PRINT', 'READ', 'RETURN', 'VOID', 'WHILE',
    )

    keyword_map = {}
    for keyword in keywords:
        keyword_map[keyword.lower()] = keyword

    # All the tokens recognized by the lexer
    tokens = (
        # identifiers
        'ID',

        # constants
        'INT_CONST', 'FLOAT_CONST',

    ) + keywords

    # Rules
    t_ignore = ' \t'

    # Newlines
    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_ID(self, t):
        r'[a-zA-Z_][0-9a-zA-Z_]*'
        t.type = self.keyword_map.get(t.value, "ID")
        return t

    def t_comment(self, t):
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count('\n')

    def t_error(self, t):
        msg = "Illegal character %s" % repr(t.value[0])
        self._error(msg, t)

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

###########################################################
## misc ###################################################
###########################################################

def print_error(msg, x, y):
    print("Lexical error: %s at %d:%d" % (msg, x, y))


m = UCLexer(error_func=print_error)
m.build()

###########################################################
## tests ##################################################
###########################################################

def test_simple_prog():
    input_text = """
        /* comment */
        int j = 3;
        int main () {
            int i = j;
            int k = 3;
            int p = 2 * j;
            assert p == 2 * i;
        }
    """
    tokens = m.scan(input_text, print_tokens=False)
    assert tokens == [
        "LexToken(INT,'int',2,14)",
        "LexToken(ID,'j',2,18)",
        "LexToken(EQUALS,'=',2,20)",
        "LexToken(ICONST,'3',2,22)",
        "LexToken(SEMI,';',2,23)",
        "LexToken(INT,'int',3,25)",
        "LexToken(ID,'main',3,29)",
        "LexToken(LPAREN,'(',3,34)",
        "LexToken(RPAREN,')',3,35)",
        "LexToken(LBRACE,'{',3,37)",
        "LexToken(INT,'int',4,41)",
        "LexToken(ID,'i',4,45)",
        "LexToken(EQUALS,'=',4,47)",
        "LexToken(ID,'j',4,49)",
        "LexToken(SEMI,';',4,50)",
        "LexToken(INT,'int',5,54)",
        "LexToken(ID,'k',5,58)",
        "LexToken(EQUALS,'=',5,60)",
        "LexToken(ICONST,'3',5,62)",
        "LexToken(SEMI,';',5,63)",
        "LexToken(INT,'int',6,67)",
        "LexToken(ID,'p',6,71)",
        "LexToken(EQUALS,'=',6,73)",
        "LexToken(ICONST,'2',6,75)",
        "LexToken(TIMES,'*',6,77)",
        "LexToken(ID,'j',6,79)",
        "LexToken(SEMI,';',6,80)",
        "LexToken(ASSERT,'assert',7,84)",
        "LexToken(ID,'p',7,91)",
        "LexToken(EQ,'==',7,93)",
        "LexToken(ICONST,'2',7,96)",
        "LexToken(TIMES,'*',7,98)",
        "LexToken(ID,'i',7,100)",
        "LexToken(SEMI,';',7,101)",
        "LexToken(RBRACE,'}',8,103)",
    ]

def test_for_loop():
    input_text = """
        for (int i = 0; i < 100; i++)
            (*a)[i];
    """
    tokens = m.scan(input_text, print_tokens=False)
    assert True

def test_ptrs():
    input_text = """
        int a=10;
        int *p;
        p = &a;
        int b = *p;
    """
    tokens = m.scan(input_text, print_tokens=False)
    assert True

def test_array():
    input_text = """
        int v[5] = { 1, 3, 5, 7, 9};
        assert v[3] == 7;
    """
    tokens = m.scan(input_text, print_tokens=False)
    assert True

def test_array_ptr():
    input_text = """
        float (*foo)[3] = &(float[]){ 0.5, 1., -0.5 };
    """
    tokens = m.scan(input_text, print_tokens=False)
    assert True

def test_function_variable():
    input_text = """
        int (*operation)(int x, int y);
    """
    tokens = m.scan(input_text, print_tokens=False)
    assert True