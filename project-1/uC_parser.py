import re
import ply.yacc as yacc

from uC_lexer import UCLexer
from uC_AST import Program

# NOTE Each rule is defined by a function whose docstring contains the appropriate context-free grammar specification.
#      The statements that make up the function body implement the semantic actions of the rule.
#      Each function accepts a single argument `p` that is a sequence containing the values of each grammar symbol
#      in the corresponding rule. The values of `p[i]` are mapped to grammar symbols, in order.

# NOTE The first rule defined in the yacc specification determines the starting grammar symbol, unless `start` is declared.
#      The `p_error(p)` rule is defined to catch syntax errors.

# NOTE To resolve ambiguity, individual tokens can be assigned a precedence level and their associativity direction.
#      This is done by adding a variable `precedence` to the grammar file.
#      Within the precedence declaration, tokens are ordered from lowest to highest precedence.

# NOTE When shift/reduce conflicts are encountered, the parser looks at the precedence rules and associativity specifiers:
#      1. If the current token has higher precedence than the rule on the stack, it is shifted.
#      2. If the grammar rule on the stack has higher precedence, the rule is reduced.
#      3. If the current token and the grammar rule have the same precedence, the rule is reduced for left associativity,
#         whereas the token is shifted for right associativity.
#      4. If nothing is known about the precedence, shift/reduce conflicts are resolved in favor of shifting (the default).

# NOTE By default, PLY tracks the line number and position of all tokens, which are available using the following functions:
#       - p.lineno(num), Return the line number for symbol num.
#       - p.lexpos(num), Return the lexing position for symbol num.

# NOTE See '%prec' and 'nonassoc' in section 6.6 (https://www.dabeaz.com/ply/ply.html#ply_nn27).
#      See the last example in section 6.11 (https://www.dabeaz.com/ply/ply.html#ply_nn35b).

###########################################################
## uC Parser ##############################################
###########################################################

class UCParser:

    start = 'program' # top level rule

    def p_empty(self, p):
        ''' empty : '''
        p[0] = None

    def p_error(self, p):
        if p is not None:
            print("Error near symbol '%s'" % p.value)
        else:
            print("Error at the end of input")

    ##
    ## <program> ::= {<global_declaration>}+
    ##

    def p_program(self, p):
        ''' program : global_declaration_list '''
        p[0] = Program(p[1])

    def p_global_declaration_list(self, p):
        ''' global_declaration_list : global_declaration
                                    | global_declaration_list global_declaration
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    ##
    ## <global_declaration> ::= <function_definition>
    ##                        | <declaration>
    ##

    def p_global_declaration(self, p):
        ''' global_declaration : function_definition
                               | declaration
        '''
        pass

    ##
    ## <function_definition> ::= {<type_specifier>}? <declarator> {<declaration>}* <compound_statement>
    ##

    def p_function_definition_01(self, p):
        ''' function_definition : declarator declaration_list_opt compound_statement
                                | declaration
        '''
        pass

    def p_function_definition_02(self, p):
        ''' function_definition : type_specifier declarator declaration_list_opt compound_statement
                                | declaration
        '''
        pass

    def p_declaration_list_opt(self, p):
        ''' declaration_list_opt : empty
                                 | declaration_list
        '''
        p[0] = p[1]

    ##
    ## <type_specifier> ::= void
    ##                    | char
    ##                    | int
    ##                    | float
    ##

    def p_type_specifier(self, p):
        ''' type_specifier : VOID
                           | CHAR
                           | INT
                           | FLOAT
        '''
        pass

    ##
    ## <declarator> ::= <identifier>
    ##                | ( <declarator> )
    ##                | <declarator> [ {<constant_expression>}? ]
    ##                | <declarator> ( <parameter_list> )
    ##                | <declarator> ( {<identifier>}* )
    ##

    def p_declarator(self, p):
        ''' declarator : identifier
                       | LPAREN declarator RPAREN
                       | declarator LBRACKET RBRACKET
                       | declarator LBRACKET constant_expression_list RBRACKET
                       | declarator LPAREN parameter_list RPAREN
                       | declarator LPAREN identifier_list_opt RPAREN
        '''
        pass

    ##
    ## <constant_expression> ::= <binary_expression>
    ##

    def p_type_specifier(self, p):
        ''' constant_expression : binary_expression '''
        pass

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

    def p_binary_expression(self, p):
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

    def p_binary_expression(self, p):
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

    def p_unary_expression(self, p):
        ''' unary_expression : postfix_expression
                             | PLUSPLUS unary_expression
                             | MINUSMINUS unary_expression
                             | unary_expression cast_expression
        '''
        pass

    ##
    ## <postfix_expression> ::= <primary_expression>
    ##                        | <postfix_expression> [ <expression> ]
    ##                        | <postfix_expression> ( {<assignment_expression>}* )
    ##                        | <postfix_expression> ++
    ##                        | <postfix_expression> --
    ##

    def p_postfix_expression(self, p):
        ''' postfix_expression : primary_expression
                               | postfix_expression LBRACKET expression RBRACKET
                               | postfix_expression LPAREN assignment_expression_list_opt RPAREN
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

    def p_primary_expression(self, p):
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

    def p_constant(self, p):
        ''' constant : integer_constant
                     | character_constant
                     | floating_constant
        '''
        pass

    ##
    ## <expression> ::= <assignment_expression>
    ##                | <expression> , <assignment_expression>
    ##

    def p_expression(self, p):
        ''' constant : assignment_expression
                     | expression COMMA assignment_expression
        '''
        pass

    ##
    ## <assignment_expression> ::= <binary_expression>
    ##                           | <unary_expression> <assignment_operator> <assignment_expression>
    ##

    def p_assignment_expression(self, p):
        ''' assignment_expression : binary_expression
                                  | unary_expression assignment_operator assignment_expression
        '''
        pass

    ##
    ## <assignment_operator> ::= =
    ##                         | *=
    ##                         | /=
    ##                         | %=
    ##                         | +=
    ##                         | -=
    ##

    def p_assignment_expression(self, p):
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

    def p_unary_operator(self, p):
        ''' assignment_operator : AND
                                | TIMES
                                | PLUS
                                | MINUS
                                | NOT
        '''
        pass # FIXME add ++ and -- (?)

    ##
    ## <parameter_list> ::= <parameter_declaration>
    ##                    | <parameter_list> , <parameter_declaration>
    ##

    def p_parameter_list(self, p):
        ''' parameter_list : parameter_declaration
                           | parameter_list COMMA parameter_declaration
        '''
        pass

    ##
    ## <parameter_declaration> ::= <type_specifier> <declarator>
    ##

    def p_parameter_declaration(self, p):
        ''' parameter_list : type_specifier declarator '''
        pass

    ##
    ## <declaration> ::=  <type_specifier> {<init_declarator>}* ;
    ##

    def p_declaration(self, p):
        ''' declaration : type_specifier init_declarator_list_opt '''
        pass

    ##
    ## <init_declarator> ::= <declarator>
    ##                     | <declarator> = <initializer>
    ##

    def p_declaration(self, p):
        ''' init_declarator : declarator
                            | declarator EQUALS initializer
        '''
        pass

    ##
    ## <initializer> ::= <assignment_expression>
    ##                 | { <initializer_list> }
    ##                 | { <initializer_list> , }
    ##

    def p_initializer(self, p):
        ''' initializer : assignment_expression
                        | LBRACE initializer_list RBRACE
                        | LBRACE initializer_list COMMA RBRACE
        '''
        pass

    ##
    ## <initializer_list> ::= <initializer>
    ##                      | <initializer_list> , <initializer>
    ##

    def p_initializer_list(self, p):
        ''' initializer_list : initializer
                             | initializer_list COMMA initializer
        '''
        pass

    ##
    ## <compound_statement> ::= { {<declaration>}* {<statement>}* }
    ##

    def p_compound_statement(self, p):
        ''' compound_statement : LBRACE declaration_list_opt statement_list_opt RBRACE '''
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

    def p_compound_statement(self, p):
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

    ##
    ## <expression_statement> ::= {<expression>}? ;
    ##

    def p_compound_statement(self, p):
        ''' expression_statement : empty
                                 | expression
        '''
        pass

    ##
    ## <selection_statement> ::= if ( <expression> ) <statement>
    ##                         | if ( <expression> ) <statement> else <statement>
    ##

    def p_selection_statement(self, p):
        ''' selection_statement : IF LPAREN expression RPAREN statement
                                | IF LPAREN expression RPAREN statement ELSE statement
        '''
        pass

    ##
    ## <iteration_statement> ::= while ( <expression> ) <statement>
    ##                         | for ( {<expression>}? ; {<expression>}? ; {<expression>}? ) <statement>
    ##

    ##
    ## <jump_statement> ::= break ;
    ##                    | return {<expression>}? ;
    ##

    ##
    ## <assert_statement> ::= assert <expression> ;
    ##

    ##
    ## <print_statement> ::= print ( {<expression>}* ) ;
    ##

    ##
    ## <read_statement> ::= read ( {<declarator>}+ );