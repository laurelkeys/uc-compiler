## <constant_expression> ::= <binary_expression>
def p_constant_expression(p):
    ''' constant_expression : binary_expression '''
    p[0] = p[1]
def p_constant_expression__opt(p):
    ''' constant_expression__opt : empty
                                 | constant_expression
    '''
    p[0] = p[1]

## <declarator> ::= <identifier>
##                | ( <declarator> )
##                | <declarator> [ {<constant_expression>}? ]
##                | <declarator> ( <parameter_list> )
##                | <declarator> ( {<identifier>}* )
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

## <parameter_list> ::= <parameter_declaration>
##                    | <parameter_list> , <parameter_declaration>
def p_parameter_list(p):
    ''' parameter_list : parameter_declaration
                       | parameter_list COMMA parameter_declaration
    '''
    pass

## <parameter_declaration> ::= <type_specifier> <declarator>
def p_parameter_declaration(p):
    ''' parameter_declaration : type_specifier declarator '''
    pass

#############################

## <declaration> ::=  <type_specifier> {<init_declarator>}* ;
def p_declaration(p):
    ''' declaration : type_specifier init_declarator__list__opt SEMI '''
    pass
    # FIXME https://github.com/eliben/pycparser/blob/master/pycparser/c_parser.py#L425
    # if p[2] is None:
    #     p[0] = self._build_declarations(spec=p[1], decls=[dict(decl=None, init=None)])
    # else:
    #     p[0] = self._build_declarations(spec=p[1], decls=p[2])

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
    # FIXME ?
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

#############################

## <compound_statement> ::= { {<declaration>}* {<statement>}* }
def p_compound_statement(p):
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

## <expression_statement> ::= {<expression>}? ;
def p_expression_statement(p):
    ''' expression_statement : expression__opt '''
    p[0] = p[1]

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

## <print_statement> ::= print ( {<expression>}* ) ;
def p_print_statement(p):
    ''' print_statement : PRINT LPAREN expression__list__opt RPAREN SEMI '''
    p[0] = Print(p[3])

## <read_statement> ::= read ( {<declarator>}+ ) ;
def p_read_statement(p):
    ''' read_statement : READ LPAREN declarator__list RPAREN SEMI '''
    p[0] = Read(p[3])

#############################

## <program> ::= {<global_declaration>}+
def p_program(p): # NOTE this is the top level rule, as defined by `start`
    ''' program : global_declaration__list '''
    p[0] = Program(p[1])

## <global_declaration> ::= <function_definition>
##                        | <declaration>
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

## <function_definition> ::= {<type_specifier>}? <declarator> {<declaration>}* <compound_statement>
def p_function_definition(p):
    ''' function_definition : type_specifier__opt declarator declaration__list__opt compound_statement '''
    pass
