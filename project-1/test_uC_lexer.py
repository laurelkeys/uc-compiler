from uC_lexer import UCLexer

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

# NOTE For the purpose of debugging, you can run lex() in a debugging mode as follows:
#           lexer = lex.lex(debug=1)
#
#      This will produce various sorts of debugging information including all of the added rules,
#      the master regular expressions used by the lexer, and tokens generating during lexing.
#
#      In addition, lex.py comes with a simple main function which will either tokenize input read from standard input
#      or from a file specified on the command line. To use it, simply put this in your lexer:
#           if __name__ == '__main__':
#               lex.runmain()

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
    # FIXME we're comparing LexToken with strings,
    #       and the line and column might be different (by some constant)
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

# ref.: http://www.dabeaz.com/ply/ply.html#ply_nn3
#       https://github.com/iviarcio/mc921/blob/master/lex_unit_tests.ipynb
#       https://en.wikipedia.org/wiki/Operators_in_C_and_C%2B%2B#Operator_precedence
