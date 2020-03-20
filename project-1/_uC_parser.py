import re
import ply.yacc as yacc

from uC_lexer import UCLexer

tokens = UCLexer.tokens

##
## <program> ::= {<global_declaration>}+
##

def p_program(p): # NOTE keep this as the top level rule
    ''' program : global_declaration__list '''
    pass

##
def p_empty(p):
    ''' empty : '''
    p[0] = None

##
def p_error(p):
    if p is not None:
        print("Error near symbol '%s'" % p.value)
    else:
        print("Error at the end of input")

## <integer_constant>
def p_integer_constant(p):
    ''' integer_constant : INT_CONST '''
    pass

## <floating_constant>
def p_floating_constant(p):
    ''' floating_constant : FLOAT_CONST '''
    pass

## <character_constant>
def p_character_constant(p):
    ''' character_constant : CHAR_CONST '''
    pass

## <string>
def p_string(p):
    """ string : STRING_LITERAL """
    pass

## <identifier>
def p_identifier(p):
    """ identifier : ID """
    pass

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

##
## <global_declaration> ::= <function_definition>
##                        | <declaration>
##

def p_global_declaration(p):
    ''' global_declaration : function_definition
                            | declaration
    '''
    pass

def p_global_declaration__list(p):
    ''' global_declaration__list : global_declaration
                                    | global_declaration__list global_declaration
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

##
## <function_definition> ::= {<type_specifier>}? <declarator> {<declaration>}* <compound_statement>
##

def p_function_definition(p):
    ''' function_definition : type_specifier__opt declarator declaration__list__opt compound_statement '''
    pass

##
## <type_specifier> ::= void
##                    | char
##                    | int
##                    | float
##

def p_type_specifier(p):
    ''' type_specifier : VOID
                        | CHAR
                        | INT
                        | FLOAT
    '''
    pass

def p_type_specifier__opt(p):
    ''' type_specifier__opt : empty
                            | type_specifier
    '''
    p[0] = p[1]

##
## <declarator> ::= <identifier>
##                | ( <declarator> )
##                | <declarator> [ {<constant_expression>}? ]
##                | <declarator> ( <parameter_list> )
##                | <declarator> ( {<identifier>}* )
##

def p_declarator(p):
    ''' declarator : identifier
                    | LPAREN declarator RPAREN
                    | declarator LBRACKET constant_expression__opt RBRACKET
                    | declarator LPAREN parameter_list RPAREN
                    | declarator LPAREN identifier__list__opt RPAREN
    '''
    pass

def p_declarator__list(p):
    ''' declarator__list : declarator
                            | declarator__list declarator
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

##
## <constant_expression> ::= <binary_expression>
##

def p_constant_expression(p):
    ''' constant_expression : binary_expression '''
    pass

def p_constant_expression__opt(p):
    ''' constant_expression__opt : empty
                                    | constant_expression
    '''
    p[0] = p[1]

##
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
##

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
    pass

##
## <cast_expression> ::= <unary_expression>
##                     | ( <type_specifier> ) <cast_expression>
##

def p_cast_expression(p):
    ''' cast_expression : unary_expression
                        | LPAREN type_specifier RPAREN cast_expression
    '''
    pass

##
## <unary_expression> ::= <postfix_expression>
##                      | ++ <unary_expression>
##                      | -- <unary_expression>
##                      | <unary_operator> <cast_expression>
##

def p_unary_expression(p):
    ''' unary_expression : postfix_expression
                            | PLUSPLUS unary_expression
                            | MINUSMINUS unary_expression
                            | unary_operator cast_expression
    '''
    pass

##
## <postfix_expression> ::= <primary_expression>
##                        | <postfix_expression> [ <expression> ]
##                        | <postfix_expression> ( {<assignment_expression>}* )
##                        | <postfix_expression> ++
##                        | <postfix_expression> --
##

def p_postfix_expression(p):
    ''' postfix_expression : primary_expression
                            | postfix_expression LBRACKET expression RBRACKET
                            | postfix_expression LPAREN assignment_expression__list__opt RPAREN
                            | postfix_expression PLUSPLUS
                            | postfix_expression MINUSMINUS
    '''
    pass

##
## <primary_expression> ::= <identifier>
##                        | <constant>
##                        | <string>
##                        | ( <expression> )
##

def p_primary_expression(p):
    ''' primary_expression : identifier
                            | constant
                            | string
                            | LPAREN expression RPAREN
    '''
    pass

##
## <constant> ::= <integer_constant>
##              | <character_constant>
##              | <floating_constant>
##

def p_constant(p):
    ''' constant : integer_constant
                    | character_constant
                    | floating_constant
    '''
    pass

##
## <expression> ::= <assignment_expression>
##                | <expression> , <assignment_expression>
##

def p_expression(p):
    ''' expression : assignment_expression
                    | expression COMMA assignment_expression
    '''
    pass

def p_expression__list__opt(p):
    ''' expression__list__opt : empty
                                | expression__list
    '''
    p[0] = p[1]

def p_expression__list(p):
    ''' expression__list : expression
                            | expression__list expression
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

def p_expression__opt(p):
    ''' expression__opt : empty
                        | expression
    '''
    p[0] = p[1]

##
## <assignment_expression> ::= <binary_expression>
##                           | <unary_expression> <assignment_operator> <assignment_expression>
##

def p_assignment_expression(p):
    ''' assignment_expression : binary_expression
                                | unary_expression assignment_operator assignment_expression
    '''
    pass

def p_assignment_expression__list__opt(p):
    ''' assignment_expression__list__opt : empty
                                            | assignment_expression__list
    '''
    p[0] = p[1]

def p_assignment_expression__list(p):
    ''' assignment_expression__list : assignment_expression
                                    | assignment_expression__list assignment_expression
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

##
## <assignment_operator> ::= =
##                         | *=
##                         | /=
##                         | %=
##                         | +=
##                         | -=
##

def p_assignment_operator(p):
    ''' assignment_operator : EQUALS
                            | TIMESEQUALS
                            | DIVEQUALS
                            | MODEQUALS
                            | PLUSEQUALS
                            | MINUSEQUALS
    '''
    pass

##
## <unary_operator> ::= &
##                    | *
##                    | +
##                    | -
##                    | !
##

def p_unary_operator(p):
    ''' unary_operator : ADDRESS
                        | TIMES
                        | PLUS
                        | MINUS
                        | NOT
    '''
    pass

##
## <parameter_list> ::= <parameter_declaration>
##                    | <parameter_list> , <parameter_declaration>
##

def p_parameter_list(p):
    ''' parameter_list : parameter_declaration
                        | parameter_list COMMA parameter_declaration
    '''
    pass

##
## <parameter_declaration> ::= <type_specifier> <declarator>
##

def p_parameter_declaration(p):
    ''' parameter_declaration : type_specifier declarator '''
    pass

##
## <declaration> ::=  <type_specifier> {<init_declarator>}* ;
##

def p_declaration(p):
    ''' declaration : type_specifier init_declarator__list__opt SEMI '''
    pass

def p_declaration__list__opt(p):
    ''' declaration__list__opt : empty
                                | declaration__list
    '''
    p[0] = p[1]

def p_declaration__list(p):
    ''' declaration__list : declaration
                            | declaration__list declaration
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

##
## <init_declarator> ::= <declarator>
##                     | <declarator> = <initializer>
##

def p_init_declarator(p):
    ''' init_declarator : declarator
                        | declarator EQUALS initializer
    '''
    pass

def p_init_declarator__list__opt(p):
    ''' init_declarator__list__opt : empty
                                    | init_declarator__list
    '''
    p[0] = p[1]

def p_init_declarator__list(p):
    ''' init_declarator__list : init_declarator
                                | init_declarator__list init_declarator
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

##
## <initializer> ::= <assignment_expression>
##                 | { <initializer_list> }
##                 | { <initializer_list> , }
##

def p_initializer(p):
    ''' initializer : assignment_expression
                    | LBRACE initializer_list RBRACE
                    | LBRACE initializer_list COMMA RBRACE
    '''
    pass

##
## <initializer_list> ::= <initializer>
##                      | <initializer_list> , <initializer>
##

def p_initializer_list(p):
    ''' initializer_list : initializer
                            | initializer_list COMMA initializer
    '''
    pass

##
## <compound_statement> ::= { {<declaration>}* {<statement>}* }
##

def p_compound_statement(p):
    ''' compound_statement : LBRACE declaration__list__opt statement__list__opt RBRACE '''
    pass

##
## <statement> ::= <expression_statement>
##               | <compound_statement>
##               | <selection_statement>
##               | <iteration_statement>
##               | <jump_statement>
##               | <assert_statement>
##               | <print_statement>
##               | <read_statement>
##

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
    pass

def p_statement__list__opt(p):
    ''' statement__list__opt : empty
                                | statement__list
    '''
    p[0] = p[1]

def p_statement__list(p):
    ''' statement__list : statement
                        | statement__list statement
    '''
    p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

##
## <expression_statement> ::= {<expression>}? ;
##

def p_expression_statement(p):
    ''' expression_statement : expression__opt '''
    pass

##
## <selection_statement> ::= if ( <expression> ) <statement>
##                         | if ( <expression> ) <statement> else <statement>
##

def p_selection_statement(p):
    ''' selection_statement : IF LPAREN expression RPAREN statement
                            | IF LPAREN expression RPAREN statement ELSE statement
    '''
    pass

##
## <iteration_statement> ::= while ( <expression> ) <statement>
##                         | for ( {<expression>}? ; {<expression>}? ; {<expression>}? ) <statement>
##

def p_iteration_statement(p):
    ''' iteration_statement : WHILE LPAREN expression RPAREN
                            | FOR LPAREN expression__opt SEMI expression__opt SEMI expression__opt RPAREN SEMI
    '''
    pass

##
## <jump_statement> ::= break ;
##                    | return {<expression>}? ;
##

def p_jump_statement(p):
    ''' jump_statement : BREAK SEMI
                        | RETURN expression__opt SEMI
    '''
    pass

##
## <assert_statement> ::= assert <expression> ;
##

def p_assert_statement(p):
    ''' assert_statement : ASSERT expression SEMI '''
    pass

##
## <print_statement> ::= print ( {<expression>}* ) ;
##

def p_print_statement(p):
    ''' print_statement : PRINT LPAREN expression__list__opt RPAREN SEMI '''
    pass

##
## <read_statement> ::= read ( {<declarator>}+ ) ;
##

def p_read_statement(p):
    ''' read_statement : READ LPAREN declarator__list RPAREN SEMI '''
    pass

parser = yacc.yacc()