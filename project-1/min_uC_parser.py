import re
import ply.yacc as yacc

from uC_lexer import UCLexer
from uC_AST import *


# NOTE tokens are ordered from lowest to highest precedence
precedence = (
    ('left', 'COMMA'),

    ('right', 'TIMESEQUALS', 'DIVEQUALS', 'MODEQUALS'),
    ('right', 'PLUSEQUALS', 'MINUSEQUALS'),
    ('right', 'EQUALS'),

    ('left', 'OR'),
    ('left', 'AND'),

    ('left', 'EQ', 'NEQ'),
    ('left', 'GT', 'GEQ', 'LT', 'LEQ'),

    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIV', 'MOD'),

    ('right', 'ADDRESS'),
    ('right', '__DEREFERENCE'), # indirection
    ('right', 'NOT'),
    ('right', '__UPLUS', '__UMINUS'), # unary plus and minus
    ('right', '__pre_PLUSPLUS', '__pre_MINUSMINUS'), # prefix increment and decrement

    ('left', '__post_PLUSPLUS', '__post_MINUSMINUS'), # suffix/postfix increment and decrement
)

###########################################################

def _type_modify_decl(self, decl, modifier):
    # TODO https://github.com/eliben/pycparser/blob/master/pycparser/c_parser.py#L251
    pass

def _build_declarations(spec, decls):
        ''' Builds a list of declarations all sharing the given specifiers. '''
        declarations = []

        for decl in decls:
            assert decl['decl'] is not None
            declaration = Decl(
                name=None,
                type=decl['decl'],
                init=decl.get('init'),
                # coord=decl['decl'].coord
            )

            fixed_decl = declaration # FIXME
            # if isinstance(declaration.type, Type):
            #     fixed_decl = declaration
            # else:
            #     fixed_decl = _fix_decl_name_type(declaration, spec)
            # TODO https://github.com/eliben/pycparser/blob/master/pycparser/c_parser.py#L375

            declarations.append(fixed_decl)

        return declarations

def _build_function_definition(spec, decl, param_decls, body):
    ''' Builds a function definition. '''
    declaration, *_ = _build_declarations(
        spec=spec,
        decls=[dict(decl=decl, init=None)]
    )

    return FuncDef(
        decl=declaration,
        param_decls=param_decls,
        body=body,
        # coord=decl.coord
    )

###########################################################

def p_empty(p):
    ''' empty : '''
    p[0] = None

###########################################################

# <identifier>
def p_identifier(p):
    """ identifier : ID """
    p[0] = ID(p[1], lineno=p.lineno(1))
def p_identifier__list__opt(p):
    ''' identifier__list__opt : empty
                              | identifier__list
    '''
    p[0] = p[1]
def p_identifier__list(p):
    ''' identifier__list : identifier
                         | identifier__list identifier
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

# <string>
def p_string(p):
    """ string : STRING_LITERAL """
    p[0] = Constant("string", p[1])

# <integer_constant>
def p_integer_constant(p):
    ''' integer_constant : INT_CONST '''
    p[0] = Constant("int", p[1])
# <character_constant>
def p_character_constant(p):
    ''' character_constant : CHAR_CONST '''
    p[0] = Constant("char", p[1])
# <floating_constant>
def p_floating_constant(p):
    ''' floating_constant : FLOAT_CONST '''
    p[0] = Constant("float", p[1])

## <constant> ::= <integer_constant>
##              | <character_constant>
##              | <floating_constant>
def p_constant(p):
    ''' constant : integer_constant
                 | character_constant
                 | floating_constant
    '''
    p[0]= p[1]

## <type_specifier> ::= void
##                    | char
##                    | int
##                    | float
def p_type_specifier(p):
    ''' type_specifier : VOID
                       | CHAR
                       | INT
                       | FLOAT
    '''
    p[0] = Type(p[1])

## <assignment_operator> ::= =
##                         | *=
##                         | /=
##                         | %=
##                         | +=
##                         | -=
def p_assignment_operator(p):
    ''' assignment_operator : EQUALS
                            | TIMESEQUALS
                            | DIVEQUALS
                            | MODEQUALS
                            | PLUSEQUALS
                            | MINUSEQUALS
    '''
    p[0] = p[1]

## <unary_operator> ::= &
##                    | *
##                    | +
##                    | -
##                    | !
def p_unary_operator(p):
    ''' unary_operator : ADDRESS
                       | TIMES %prec __DEREFERENCE
                       | PLUS %prec __UPLUS
                       | MINUS %prec __UMINUS
                       | NOT
    '''
    p[0] = p[1]

###########################################################

## <binary_expression> ::= <cast_expression>
##                       | <binary_expression> * <binary_expression>
##                       | <binary_expression> / <binary_expression>
##                       | <binary_expression> % <binary_expression>
##                       | <binary_expression> + <binary_expression>
##                       | <binary_expression> - <binary_expression>
##                       | <binary_expression> < <binary_expression>
##                       | <binary_expression> <= <binary_expression>
##                       | <binary_expression> > <binary_expression>
##                       | <binary_expression> >= <binary_expression>
##                       | <binary_expression> == <binary_expression>
##                       | <binary_expression> != <binary_expression>
##                       | <binary_expression> && <binary_expression>
##                       | <binary_expression> || <binary_expression>
def p_binary_expression(p):
    ''' binary_expression : cast_expression
                          | binary_expression TIMES binary_expression
                          | binary_expression DIV binary_expression
                          | binary_expression MOD binary_expression
                          | binary_expression PLUS binary_expression
                          | binary_expression MINUS binary_expression
                          | binary_expression LT binary_expression
                          | binary_expression LEQ binary_expression
                          | binary_expression GT binary_expression
                          | binary_expression GEQ binary_expression
                          | binary_expression EQ binary_expression
                          | binary_expression NEQ binary_expression
                          | binary_expression AND binary_expression
                          | binary_expression OR binary_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryOp(p[1], p[2], p[3])

## <cast_expression> ::= <unary_expression>
##                     | ( <type_specifier> ) <cast_expression>
def p_cast_expression(p):
    ''' cast_expression : unary_expression
                        | LPAREN type_specifier RPAREN cast_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Cast(p[2], p[4])

## <unary_expression> ::= <postfix_expression>
##                      | ++ <unary_expression>
##                      | -- <unary_expression>
##                      | <unary_operator> <cast_expression>
def p_unary_expression(p):
    ''' unary_expression : postfix_expression
                         | PLUSPLUS unary_expression %prec __pre_PLUSPLUS
                         | MINUSMINUS unary_expression %prec __pre_MINUSMINUS
                         | unary_operator cast_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = UnaryOp(p[1], p[2])

## <postfix_expression> ::= <primary_expression>
##                        | <postfix_expression> [ <expression> ]
##                        | <postfix_expression> ( {<argument_expression_list>}? )
##                        | <postfix_expression> ++
##                        | <postfix_expression> --
def p_postfix_expression(p):
    ''' postfix_expression : primary_expression
                           | postfix_expression LBRACKET expression RBRACKET
                           | postfix_expression LPAREN argument_expression_list__opt RPAREN
                           | postfix_expression PLUSPLUS %prec __post_PLUSPLUS
                           | postfix_expression MINUSMINUS %prec __post_MINUSMINUS
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 4:
        if p[2] == '[':
            p[0] = ArrayRef(p[1], p[3])
        else:
            p[0] = FuncCall(p[1], p[3])
    else:
        # NOTE a 'p' is added so we can differentiate this from when ++ or -- comes as a prefix
        p[0] = UnaryOp('p' + p[2], p[1])

## <primary_expression> ::= <identifier>
##                        | <constant>
##                        | <string>
##                        | ( <expression> )
def p_primary_expression(p):
    ''' primary_expression : identifier
                           | constant
                           | string
                           | LPAREN expression RPAREN
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]

## <expression> ::= <assignment_expression>
##                | <expression> , <assignment_expression>
def p_expression(p):
    ''' expression : assignment_expression
                   | expression COMMA assignment_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        if not isinstance(p[1], ExprList):
            p[1] = ExprList([p[1]])
        p[1].exprs.append(p[3])
        p[0] = p[1]
def p_expression__opt(p):
    ''' expression__opt : empty
                        | expression
    '''
    p[0] = p[1]

## <argument_expression_list> ::= <assignment_expression>
##                              | <argument_expression_list> , <assignment_expression>
def p_argument_expression(p):
    ''' argument_expression_list : assignment_expression
                                 | argument_expression_list COMMA assignment_expression
    '''
    if len(p) == 2:
        p[0] = ExprList([p[1]])
    else:
        p[1].exprs.append(p[3])
        p[0] = p[1]
def p_argument_expression_list__opt(p):
    ''' argument_expression_list__opt : empty
                                      | argument_expression_list
    '''
    p[0] = p[1]

## <assignment_expression> ::= <binary_expression>
##                           | <unary_expression> <assignment_operator> <assignment_expression>
def p_assignment_expression(p):
    ''' assignment_expression : binary_expression
                              | unary_expression assignment_operator assignment_expression
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Assignment(p[1], p[2], p[3])

###########################################################

## <constant_expression> ::= <binary_expression>
def p_constant_expression(p):
    ''' constant_expression : binary_expression '''
    p[0] = p[1]
def p_constant_expression__opt(p):
    ''' constant_expression__opt : empty
                                 | constant_expression
    '''
    p[0] = p[1]

## <declarator> ::= {<pointer>}? <direct_declarator>
def p_declarator(p):
    ''' declarator : pointer__opt direct_declarator '''
    if p[1] is None:
        p[0] = p[2]
    else:
        p[0] = _type_modify_decl(p[2], p[1])
    # TODO https://github.com/eliben/pycparser/blob/master/pycparser/c_parser.py#L1087

## <pointer> ::= * {<pointer>}?
def p_pointer(p):
    ''' pointer : TIMES pointer__opt %prec __DEREFERENCE '''
    # TODO https://github.com/eliben/pycparser/blob/master/pycparser/c_parser.py#L1199
    pass
def p_pointer__opt(p):
    ''' pointer__opt : empty
                     | pointer
    '''
    p[0] = p[1]

## <direct_declarator> ::= <identifier>
##                       | ( <declarator> )
##                       | <direct_declarator> [ {<constant_expression>}? ]
##                       | <direct_declarator> ( <parameter_list> )
##                       | <direct_declarator> ( {<identifier>}* )
def p_direct_declarator(p):
    ''' direct_declarator : identifier
                          | LPAREN declarator RPAREN
                          | direct_declarator LBRACKET constant_expression__opt RBRACKET
                          | direct_declarator LPAREN parameter_list RPAREN
                          | direct_declarator LPAREN identifier__list__opt RPAREN
    '''
    # TODO https://github.com/eliben/pycparser/blob/master/pycparser/c_parser.py#L1087
    pass

## <parameter_list> ::= <parameter_declaration>
##                    | <parameter_list> , <parameter_declaration>
def p_parameter_list(p):
    ''' parameter_list : parameter_declaration
                       | parameter_list COMMA parameter_declaration
    '''
    if len(p) == 2:
        p[0] = ParamList([p[1]])
    else:
        p[1].params.append(p[3])
        p[0] = p[1]

## <parameter_declaration> ::= <type_specifier> <declarator>
def p_parameter_declaration(p):
    ''' parameter_declaration : type_specifier declarator '''
    # TODO https://github.com/eliben/pycparser/blob/master/pycparser/c_parser.py#L1264
    pass

###########################################################

## <initializer> ::= <assignment_expression>
##                 | { <initializer_list> }
##                 | { <initializer_list> , }
def p_initializer(p):
    ''' initializer : assignment_expression
                    | LBRACE initializer_list RBRACE
                    | LBRACE initializer_list COMMA RBRACE
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]

## <initializer_list> ::= <initializer>
##                      | <initializer_list> , <initializer>
def p_initializer_list(p):
    ''' initializer_list : initializer
                         | initializer_list COMMA initializer
    '''
    if len(p) == 2:
        p[0] = InitList([p[1]])
    else:
        if not isinstance(p[1], InitList):
            p[1] = InitList([p[1]])
        p[1].exprs.append(p[3])
        p[0] = p[1]

###########################################################

## <init_declarator> ::= <declarator>
##                     | <declarator> = <initializer>
def p_init_declarator(p):
    ''' init_declarator : declarator
                        | declarator EQUALS initializer
    '''
    if len(p) == 2:
        p[0] = dict(decl=p[1], init=None)
    else:
        p[0] = dict(decl=p[1], init=p[3])

## <init_declarator_list> ::= <init_declarator>
##                          | <init_declarator_list> , <init_declarator>
def p_init_declarator_list(p):
    ''' init_declarator_list : init_declarator
                             | init_declarator_list COMMA init_declarator
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]
def p_init_declarator_list__opt(p):
    ''' init_declarator_list__opt : empty
                                  | init_declarator_list
    '''
    p[0] = p[1]

###########################################################

## <declaration> ::=  <type_specifier> {<init_declarator_list>}? ;
def p_declaration(p):
    ''' declaration : type_specifier init_declarator_list__opt SEMI '''
    # TODO https://github.com/eliben/pycparser/blob/master/pycparser/c_parser.py#L740
    pass
    # if p[2] is None:
    #     p[0] = self._build_declarations(spec=p[1], decls=[dict(decl=None, init=None)])
    # else:
    #     p[0] = self._build_declarations(spec=p[1], decls=p[2])
def p_declaration__list(p):
    ''' declaration__list : declaration
                          | declaration__list declaration
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]
def p_declaration__list__opt(p):
    ''' declaration__list__opt : empty
                               | declaration__list
    '''
    p[0] = p[1]

###########################################################

## <expression_statement> ::= {<expression>}? ;
def p_expression_statement(p):
    ''' expression_statement : expression__opt SEMI '''
    p[0] = p[1]

## <jump_statement> ::= break ;
##                    | return {<expression>}? ;
def p_jump_statement(p):
    ''' jump_statement : BREAK SEMI
                       | RETURN expression__opt SEMI
    '''
    if len(p) == 3:
        p[0] = Break()
    else:
        p[0] = Return(p[2])

## <assert_statement> ::= assert <expression> ;
def p_assert_statement(p):
    ''' assert_statement : ASSERT expression SEMI '''
    p[0] = Assert(p[2])

## <print_statement> ::= print ( {<argument_expression_list>}? ) ;
def p_print_statement(p):
    ''' print_statement : PRINT LPAREN argument_expression_list__opt RPAREN SEMI '''
    # NOTE I've changed this rule (it's not like in uC_Grammar.ipynb)
    p[0] = Print(p[3])

## <read_statement> ::= read ( <argument_expression_list> ) ;
def p_read_statement(p):
    ''' read_statement : READ LPAREN argument_expression_list RPAREN SEMI '''
    p[0] = Read(p[3])

###########################################################

## <iteration_statement> ::= while ( <expression> ) <statement>
##                         | for ( {<expression>}? ; {<expression>}? ; {<expression>}? ) <statement>
def p_iteration_statement(p):
    ''' iteration_statement : WHILE LPAREN expression RPAREN statement
                            | FOR LPAREN expression__opt SEMI expression__opt SEMI expression__opt RPAREN statement
    '''
    if len(p) == 5:
        p[0] = While(p[3], p[5])
    else:
        p[0] = For(p[3], p[5], p[7], p[9])

## <selection_statement> ::= if ( <expression> ) <statement>
##                         | if ( <expression> ) <statement> else <statement>
def p_selection_statement(p):
    ''' selection_statement : IF LPAREN expression RPAREN statement
                            | IF LPAREN expression RPAREN statement ELSE statement
    '''
    if len(p) == 6:
        p[0] = If(p[3], p[5], None)
    else:
        p[0] = If(p[3], p[5], p[6])

###########################################################

## <compound_statement> ::= { {<declaration>}* {<statement>}* }
def p_compound_statement(p):
    ''' compound_statement : LBRACE declaration__list__opt statement__list__opt RBRACE '''
    p[0] = Compound(p[2], p[3])

# FIXME adding compound_statement generates over 100 shift/reduce conflicts
#                  | compound_statement
def p_statement(p):
    ''' statement : expression_statement
                  | compound_statement
                  | selection_statement
                  | iteration_statement
                  | jump_statement
                  | assert_statement
                  | print_statement
                  | read_statement
    '''
    p[0] = p[1]
def p_statement__list(p):
    ''' statement__list : statement
                        | statement__list statement
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]
def p_statement__list__opt(p):
    ''' statement__list__opt : empty
                             | statement__list
    '''
    p[0] = p[1]

###########################################################

def p_error(p):
    if p is not None:
        print("Error near symbol '%s'" % p.value)
    else:
        print("Error at the end of input")

###########################################################

if __name__ == "__main__":
    # top level rule
    #start = 'declaration'
    start = 'statement'

    tokens = UCLexer.tokens

    parser = yacc.yacc()