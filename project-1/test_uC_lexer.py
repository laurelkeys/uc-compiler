import re

from ply.lex import LexToken

from uC_lexer import UCLexer

###########################################################
## misc ###################################################
###########################################################

def str2tok(tok_string):
    t = LexToken()
    t.type, t.value, t.lineno, t.lexpos = re.fullmatch(
        pattern=r'LexToken\(([A-Z_]+),\'([^\']+)\',([0-9]+),([0-9]+)\)',
        string=tok_string
    ).groups()
    return t

def print_error(msg, x, y):
    print("Lexical error: %s at %d:%d" % (msg, x, y))

m = UCLexer(error_func=print_error, cast_numbers=False) # NOTE using cast_numbers=False to comply with tests
m.build()

###########################################################
## tests ##################################################
###########################################################

PRINT_TOKENS = False

def test_simple_prog():
    input_text = '\n'.join([
        "/* comment */",
        "int j = 3;",
        "int main () {",
        "  int i = j;",
        "  int k = 3;",
        "  int p = 2 * j;",
        "  assert p == 2 * i;",
        "}",
    ])
    m._reset_lineno()

    tokens = [str(tok) for tok in  m.scan(input_text, PRINT_TOKENS)]
    assert tokens == [
        "LexToken(INT,'int',2,14)",
        "LexToken(ID,'j',2,18)",
        "LexToken(EQUALS,'=',2,20)",
        "LexToken(INT_CONST,'3',2,22)",
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
        "LexToken(INT_CONST,'3',5,62)",
        "LexToken(SEMI,';',5,63)",
        "LexToken(INT,'int',6,67)",
        "LexToken(ID,'p',6,71)",
        "LexToken(EQUALS,'=',6,73)",
        "LexToken(INT_CONST,'2',6,75)",
        "LexToken(TIMES,'*',6,77)",
        "LexToken(ID,'j',6,79)",
        "LexToken(SEMI,';',6,80)",
        "LexToken(ASSERT,'assert',7,84)",
        "LexToken(ID,'p',7,91)",
        "LexToken(EQ,'==',7,93)",
        "LexToken(INT_CONST,'2',7,96)",
        "LexToken(TIMES,'*',7,98)",
        "LexToken(ID,'i',7,100)",
        "LexToken(SEMI,';',7,101)",
        "LexToken(RBRACE,'}',8,103)",
    ]

def test_for_loop():
    input_text = '\n'.join([
        "for (int i = 0; i < 100; i++)",
        "    (*a)[i];",
    ])
    m._reset_lineno()

    tokens = [str(tok) for tok in  m.scan(input_text, PRINT_TOKENS)]
    assert tokens == [
        "LexToken(FOR,'for',1,0)",
        "LexToken(LPAREN,'(',1,4)",
        "LexToken(INT,'int',1,5)",
        "LexToken(ID,'i',1,9)",
        "LexToken(EQUALS,'=',1,11)",
        "LexToken(INT_CONST,'0',1,13)",
        "LexToken(SEMI,';',1,14)",
        "LexToken(ID,'i',1,16)",
        "LexToken(LT,'<',1,18)",
        "LexToken(INT_CONST,'100',1,20)",
        "LexToken(SEMI,';',1,23)",
        "LexToken(ID,'i',1,25)",
        "LexToken(PLUSPLUS,'++',1,26)",
        "LexToken(RPAREN,')',1,28)",
        "LexToken(LPAREN,'(',2,34)",
        "LexToken(TIMES,'*',2,35)",
        "LexToken(ID,'a',2,36)",
        "LexToken(RPAREN,')',2,37)",
        "LexToken(LBRACKET,'[',2,38)",
        "LexToken(ID,'i',2,39)",
        "LexToken(RBRACKET,']',2,40)",
        "LexToken(SEMI,';',2,41)",
    ]

def test_ptrs():
    input_text = '\n'.join([
        "int a=10;",
        "int *p;",
        "p = &a;",
        "int b = *p;",
    ])
    m._reset_lineno()

    tokens = [str(tok) for tok in  m.scan(input_text, PRINT_TOKENS)]
    assert tokens == [
        "LexToken(INT,'int',1,0)",
        "LexToken(ID,'a',1,4)",
        "LexToken(EQUALS,'=',1,5)",
        "LexToken(INT_CONST,'10',1,6)",
        "LexToken(SEMI,';',1,8)",
        "LexToken(INT,'int',2,10)",
        "LexToken(TIMES,'*',2,14)",
        "LexToken(ID,'p',2,15)",
        "LexToken(SEMI,';',2,16)",
        "LexToken(ID,'p',3,18)",
        "LexToken(EQUALS,'=',3,20)",
        "LexToken(ADDRESS,'&',3,22)",
        "LexToken(ID,'a',3,23)",
        "LexToken(SEMI,';',3,24)",
        "LexToken(INT,'int',4,26)",
        "LexToken(ID,'b',4,30)",
        "LexToken(EQUALS,'=',4,32)",
        "LexToken(TIMES,'*',4,34)",
        "LexToken(ID,'p',4,35)",
        "LexToken(SEMI,';',4,36)",
    ]

def test_array():
    input_text = '\n'.join([
        "int v[5] = { 1, 3, 5, 7, 9};",
        "assert v[3] == 7;",
    ])
    m._reset_lineno()

    tokens = [str(tok) for tok in  m.scan(input_text, PRINT_TOKENS)]
    assert tokens == [
        "LexToken(INT,'int',1,0)",
        "LexToken(ID,'v',1,4)",
        "LexToken(LBRACKET,'[',1,5)",
        "LexToken(INT_CONST,'5',1,6)",
        "LexToken(RBRACKET,']',1,7)",
        "LexToken(EQUALS,'=',1,9)",
        "LexToken(LBRACE,'{',1,11)",
        "LexToken(INT_CONST,'1',1,13)",
        "LexToken(COMMA,',',1,14)",
        "LexToken(INT_CONST,'3',1,16)",
        "LexToken(COMMA,',',1,17)",
        "LexToken(INT_CONST,'5',1,19)",
        "LexToken(COMMA,',',1,20)",
        "LexToken(INT_CONST,'7',1,22)",
        "LexToken(COMMA,',',1,23)",
        "LexToken(INT_CONST,'9',1,25)",
        "LexToken(RBRACE,'}',1,26)",
        "LexToken(SEMI,';',1,27)",
        "LexToken(ASSERT,'assert',2,29)",
        "LexToken(ID,'v',2,36)",
        "LexToken(LBRACKET,'[',2,37)",
        "LexToken(INT_CONST,'3',2,38)",
        "LexToken(RBRACKET,']',2,39)",
        "LexToken(EQ,'==',2,41)",
        "LexToken(INT_CONST,'7',2,44)",
        "LexToken(SEMI,';',2,45)",
    ]

def test_array_ptr():
    input_text = '\n'.join([
        "float (*foo)[3] = &(float[]){ 0.5, 1., -0.5 };",
    ])
    m._reset_lineno()

    tokens = [str(tok) for tok in  m.scan(input_text, PRINT_TOKENS)]
    assert tokens == [
        "LexToken(FLOAT,'float',1,0)",
        "LexToken(LPAREN,'(',1,6)",
        "LexToken(TIMES,'*',1,7)",
        "LexToken(ID,'foo',1,8)",
        "LexToken(RPAREN,')',1,11)",
        "LexToken(LBRACKET,'[',1,12)",
        "LexToken(INT_CONST,'3',1,13)",
        "LexToken(RBRACKET,']',1,14)",
        "LexToken(EQUALS,'=',1,16)",
        "LexToken(ADDRESS,'&',1,18)",
        "LexToken(LPAREN,'(',1,19)",
        "LexToken(FLOAT,'float',1,20)",
        "LexToken(LBRACKET,'[',1,25)",
        "LexToken(RBRACKET,']',1,26)",
        "LexToken(RPAREN,')',1,27)",
        "LexToken(LBRACE,'{',1,28)",
        "LexToken(FLOAT_CONST,'0.5',1,30)",
        "LexToken(COMMA,',',1,33)",
        "LexToken(FLOAT_CONST,'1.',1,35)",
        "LexToken(COMMA,',',1,37)",
        "LexToken(MINUS,'-',1,39)",
        "LexToken(FLOAT_CONST,'0.5',1,40)",
        "LexToken(RBRACE,'}',1,44)",
        "LexToken(SEMI,';',1,45)",
    ]

def test_function_variable():
    input_text = '\n'.join([
        "int (*operation)(int x, int y);",
    ])
    m._reset_lineno()

    tokens = [str(tok) for tok in  m.scan(input_text, PRINT_TOKENS)]
    assert tokens == [
        "LexToken(INT,'int',1,0)",
        "LexToken(LPAREN,'(',1,4)",
        "LexToken(TIMES,'*',1,5)",
        "LexToken(ID,'operation',1,6)",
        "LexToken(RPAREN,')',1,15)",
        "LexToken(LPAREN,'(',1,16)",
        "LexToken(INT,'int',1,17)",
        "LexToken(ID,'x',1,21)",
        "LexToken(COMMA,',',1,22)",
        "LexToken(INT,'int',1,24)",
        "LexToken(ID,'y',1,28)",
        "LexToken(RPAREN,')',1,29)",
        "LexToken(SEMI,';',1,30)",
    ]

# ref.: http://www.dabeaz.com/ply/ply.html#ply_nn3
#       https://github.com/iviarcio/mc921/blob/master/lex_unit_tests.ipynb
#       https://en.wikipedia.org/wiki/Operators_in_C_and_C%2B%2B#Operator_precedence

if __name__ == "__main__":
    PRINT_TOKENS = True

    print("# simple_prog:")
    test_simple_prog()

    print("\n# for_loop:")
    test_for_loop()

    print("\n# ptrs:")
    test_ptrs()

    print("\n# array:")
    test_array()

    print("\n# array_ptr:")
    test_array_ptr()

    print("\n# function_variable:")
    test_function_variable()