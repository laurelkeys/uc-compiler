import re
import ply.yacc as yacc

from uC_lexer import UCLexer
from uC_AST import *

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

    def __init__(self):
        self.lexer = UCLexer(
            error_func=lambda msg, x, y: print("Lexical error: %s at%d:%d" % (msg, x, y))
        )
        self.lexer.build()
        self.tokens = self.lexer.tokens
        self.precedence = (
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
        self.parser = yacc.yacc(module=self, start='program') # top level rule


    def p_error(self, p):
        if p is not None:
            print("Error near symbol '%s'" % p.value)
        else:
            print("Error at the end of input")


    def p_empty(self, p):
        ''' empty : '''
        p[0] = None


    # <integer_constant>
    def p_integer_constant(self, p):
        ''' integer_constant : INT_CONST '''
        p[0] = Constant("int", p[1])


    # <floating_constant>
    def p_floating_constant(self, p):
        ''' floating_constant : FLOAT_CONST '''
        p[0] = Constant("float", p[1])


    # <character_constant>
    def p_character_constant(self, p):
        ''' character_constant : CHAR_CONST '''
        p[0] = Constant("char", p[1])


    # <string>
    def p_string(self, p):
        ''' string : STRING_LITERAL '''
        p[0] = Constant("string", p[1])


    # <identifier>
    def p_identifier(self, p):
        ''' identifier : ID '''
        p[0] = ID(p[1], lineno=p.lineno(1))

    def p_identifier__list__opt(self, p):
        ''' identifier__list__opt : empty
                                  | identifier__list
        '''
        p[0] = p[1]

    def p_identifier__list(self, p):
        ''' identifier__list : identifier
                             | identifier__list identifier
        '''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


    ## <program> ::= {<global_declaration>}+
    def p_program(self, p): # NOTE this is the top level rule, as defined by `start`
        ''' program : global_declaration__list '''
        p[0] = Program(p[1])


    ## <global_declaration> ::= <function_definition>
    ##                        | <declaration>
    def p_global_declaration(self, p):
        ''' global_declaration : function_definition
                               | declaration
        '''
        pass

    def p_global_declaration__list(self, p):
        ''' global_declaration__list : global_declaration
                                     | global_declaration__list global_declaration
        '''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


    ## <function_definition> ::= {<type_specifier>}? <declarator> {<declaration>}* <compound_statement>
    def p_function_definition(self, p):
        ''' function_definition : type_specifier__opt declarator declaration__list__opt compound_statement '''
        pass


    ## <type_specifier> ::= void
    ##                    | char
    ##                    | int
    ##                    | float
    def p_type_specifier(self, p):
        ''' type_specifier : VOID
                           | CHAR
                           | INT
                           | FLOAT
        '''
        p[0] = Type(p[1])

    def p_type_specifier__opt(self, p):
        ''' type_specifier__opt : empty
                                | type_specifier
        '''
        p[0] = p[1]


    ## <declarator> ::= {<pointer>}? <direct_declarator>
    def p_declarator(self, p):
        ''' direct_declarator : pointer__opt direct_declarator '''
        pass

    def p_declarator__list(self, p):
        ''' declarator__list : declarator
                             | declarator__list declarator
        '''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


    ## <pointer> ::= * {<pointer>}?
    def p_pointer(self, p):
        ''' pointer : TIMES pointer__opt '''
        pass

    def p_pointer__opt(self, p):
        ''' pointer__opt : empty
                         | pointer
        '''
        p[0] = p[1]


    ## <constant_expression> ::= <binary_expression>
    def p_constant_expression(self, p):
        ''' constant_expression : binary_expression '''
        p[0] = p[1]

    def p_constant_expression__opt(self, p):
        ''' constant_expression__opt : empty
                                     | constant_expression
        '''
        p[0] = p[1]


    ## <direct_declarator> ::= <identifier>
    ##                       | ( <declarator> )
    ##                       | <direct_declarator> [ {<constant_expression>}? ]
    ##                       | <direct_declarator> ( <parameter_list> )
    ##                       | <direct_declarator> ( {<identifier>}* )
    def p_direct_declarator(self, p):
        ''' direct_declarator : identifier
                              | LPAREN declarator RPAREN
                              | direct_declarator LBRACKET constant_expression__opt RBRACKET
                              | direct_declarator LPAREN parameter_list RPAREN
                              | direct_declarator LPAREN identifier__list__opt RPAREN
        '''
        pass


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
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = BinaryOp(p[1], p[2], p[3])


    ## <cast_expression> ::= <unary_expression>
    ##                     | ( <type_specifier> ) <cast_expression>
    def p_cast_expression(self, p):
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
    def p_unary_expression(self, p):
        ''' unary_expression : postfix_expression
                             | PLUSPLUS unary_expression
                             | MINUSMINUS unary_expression
                             | unary_operator cast_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = UnaryOp(p[1], p[2])


    ## <postfix_expression> ::= <primary_expression>
    ##                        | <postfix_expression> [ <expression> ]
    ##                        | <postfix_expression> ( {<assignment_expression>}* )
    ##                        | <postfix_expression> ++
    ##                        | <postfix_expression> --
    def p_postfix_expression(self, p):
        ''' postfix_expression : primary_expression
                               | postfix_expression LBRACKET expression RBRACKET
                               | postfix_expression LPAREN assignment_expression__list__opt RPAREN
                               | postfix_expression PLUSPLUS
                               | postfix_expression MINUSMINUS
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
    def p_primary_expression(self, p):
        ''' primary_expression : identifier
                               | constant
                               | string
                               | LPAREN expression RPAREN
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[2]


    ## <constant> ::= <integer_constant>
    ##              | <character_constant>
    ##              | <floating_constant>
    def p_constant(self, p):
        ''' constant : integer_constant
                     | character_constant
                     | floating_constant
        '''
        p[0]= p[1]


    ## <expression> ::= <assignment_expression>
    ##                | <expression> , <assignment_expression>
    def p_expression(self, p):
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

    def p_expression__list__opt(self, p):
        ''' expression__list__opt : empty
                                  | expression__list
        '''
        p[0] = p[1]

    def p_expression__list(self, p):
        ''' expression__list : expression
                             | expression__list expression
        '''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]

    def p_expression__opt(self, p):
        ''' expression__opt : empty
                            | expression
        '''
        p[0] = p[1]


    ## <assignment_expression> ::= <binary_expression>
    ##                           | <unary_expression> <assignment_operator> <assignment_expression>
    def p_assignment_expression(self, p):
        ''' assignment_expression : binary_expression
                                  | unary_expression assignment_operator assignment_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = Assignment(p[1], p[2], p[3])

    def p_assignment_expression__list__opt(self, p):
        ''' assignment_expression__list__opt : empty
                                             | assignment_expression__list
        '''
        p[0] = p[1]

    def p_assignment_expression__list(self, p):
        ''' assignment_expression__list : assignment_expression
                                        | assignment_expression__list assignment_expression
        '''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


    ## <assignment_operator> ::= =
    ##                         | *=
    ##                         | /=
    ##                         | %=
    ##                         | +=
    ##                         | -=
    def p_assignment_operator(self, p):
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
    def p_unary_operator(self, p):
        ''' unary_operator : ADDRESS
                           | TIMES
                           | PLUS
                           | MINUS
                           | NOT
        '''
        p[0] = p[1]


    ## <parameter_list> ::= <parameter_declaration>
    ##                    | <parameter_list> , <parameter_declaration>
    def p_parameter_list(self, p):
        ''' parameter_list : parameter_declaration
                           | parameter_list COMMA parameter_declaration
        '''
        pass


    ## <parameter_declaration> ::= <type_specifier> <declarator>
    def p_parameter_declaration(self, p):
        ''' parameter_declaration : type_specifier declarator '''
        pass


    ## <declaration> ::=  <type_specifier> {<init_declarator>}* ;
    def p_declaration(self, p):
        ''' declaration : type_specifier init_declarator__list__opt SEMI '''
        pass
        # FIXME https://github.com/eliben/pycparser/blob/master/pycparser/c_parser.py#L425
        # if p[2] is None:
        #     p[0] = self._build_declarations(spec=p[1], decls=[dict(decl=None, init=None)])
        # else:
        #     p[0] = self._build_declarations(spec=p[1], decls=p[2])

    def p_declaration__list__opt(self, p):
        ''' declaration__list__opt : empty
                                   | declaration__list
        '''
        p[0] = p[1]

    def p_declaration__list(self, p):
        ''' declaration__list : declaration
                              | declaration__list declaration
        '''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


    ## <init_declarator> ::= <declarator>
    ##                     | <declarator> = <initializer>
    def p_init_declarator(self, p):
        ''' init_declarator : declarator
                            | declarator EQUALS initializer
        '''
        if len(p) == 2:
            p[0] = dict(decl=p[1], init=None)
        else:
            p[0] = dict(decl=p[1], init=p[3])

    def p_init_declarator__list__opt(self, p):
        ''' init_declarator__list__opt : empty
                                       | init_declarator__list
        '''
        p[0] = p[1]

    def p_init_declarator__list(self, p):
        ''' init_declarator__list : init_declarator
                                  | init_declarator__list init_declarator
        '''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


    ## <initializer> ::= <assignment_expression>
    ##                 | { <initializer_list> }
    ##                 | { <initializer_list> , }
    def p_initializer(self, p):
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
    def p_initializer_list(self, p):
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


    ## <compound_statement> ::= { {<declaration>}* {<statement>}* }
    def p_compound_statement(self, p):
        ''' compound_statement : LBRACE declaration__list__opt statement__list__opt RBRACE '''
        p[0] = Compound(p[2], p[3])


    ## <statement> ::= <expression_statement>
    ##               | <compound_statement>
    ##               | <selection_statement>
    ##               | <iteration_statement>
    ##               | <jump_statement>
    ##               | <assert_statement>
    ##               | <print_statement>
    ##               | <read_statement>
    def p_statement(self, p):
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

    def p_statement__list__opt(self, p):
        ''' statement__list__opt : empty
                                 | statement__list
        '''
        p[0] = p[1]

    def p_statement__list(self, p):
        ''' statement__list : statement
                            | statement__list statement
        '''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


    ## <expression_statement> ::= {<expression>}? ;
    def p_expression_statement(self, p):
        ''' expression_statement : expression__opt '''
        p[0] = p[1]


    ## <selection_statement> ::= if ( <expression> ) <statement>
    ##                         | if ( <expression> ) <statement> else <statement>
    def p_selection_statement(self, p):
        ''' selection_statement : IF LPAREN expression RPAREN statement
                                | IF LPAREN expression RPAREN statement ELSE statement
        '''
        if len(p) == 6:
            p[0] = If(p[3], p[5], None)
        else:
            p[0] = If(p[3], p[5], p[6])


    ## <iteration_statement> ::= while ( <expression> ) <statement>
    ##                         | for ( {<expression>}? ; {<expression>}? ; {<expression>}? ) <statement>
    def p_iteration_statement(self, p):
        ''' iteration_statement : WHILE LPAREN expression RPAREN statement
                                | FOR LPAREN expression__opt SEMI expression__opt SEMI expression__opt RPAREN statement
        '''
        if len(p) == 5:
            p[0] = While(p[3], p[5])
        else:
            p[0] = For(p[3], p[5], p[7], p[9])


    ## <jump_statement> ::= break ;
    ##                    | return {<expression>}? ;
    def p_jump_statement(self, p):
        ''' jump_statement : BREAK SEMI
                           | RETURN expression__opt SEMI
        '''
        if len(p) == 3:
            p[0] = Break()
        else:
            p[0] = Return(p[2])


    ## <assert_statement> ::= assert <expression> ;
    def p_assert_statement(self, p):
        ''' assert_statement : ASSERT expression SEMI '''
        p[0] = Assert(p[2])


    ## <print_statement> ::= print ( {<expression>}* ) ;
    def p_print_statement(self, p):
        ''' print_statement : PRINT LPAREN expression__list__opt RPAREN SEMI '''
        p[0] = Print(p[3])


    ## <read_statement> ::= read ( {<declarator>}+ ) ;
    def p_read_statement(self, p):
        ''' read_statement : READ LPAREN declarator__list RPAREN SEMI '''
        p[0] = Read(p[3])
