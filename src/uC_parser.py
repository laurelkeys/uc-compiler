import ply.yacc as yacc

from uC_AST import *
from uC_lexer import UCLexer

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

    # ref.: https://en.cppreference.com/w/c/language/operator_precedence
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


    def __init__(self):
        self.lexer = UCLexer(
            error_func=lambda msg, x, y: print("Lexical error: %s at%d:%d" % (msg, x, y))
        )
        self.lexer.build()
        self.tokens = self.lexer.tokens
        self.parser = yacc.yacc(module=self, start='program') # top level rule


    def parse(self, text, filename='', debuglevel=0):
        ''' Parses uC code and returns an AST, where:
            - `text`: A string containing the uC source code.
            - `filename`: Name of the file being parsed (for meaningful error messages).
            - `debuglevel`: Debug level to yacc.
        '''
        self.lexer.filename = filename
        self.lexer._reset_lineno()
        return self.parser.parse(input=text, lexer=self.lexer, debug=debuglevel)


    # Internal auxiliary methods
    def _token_coord(self, p, token_idx):
        last_cr = p.lexer.lexer.lexdata.rfind('\n', 0, p.lexpos(token_idx))
        if last_cr < 0:
            last_cr = -1
        column = p.lexpos(token_idx) - last_cr
        return Coord(p.lineno(token_idx), column)


    def _type_modify_decl(self, decl, modifier):
        ''' Tacks a type modifier on a declarator, and returns the modified declarator.\n
            Note: `decl` and `modifier` may be modified.
        '''
        modifier_head = modifier
        modifier_tail = modifier

        while modifier_tail.type is not None:
            modifier_tail = modifier_tail.type

        if isinstance(decl, VarDecl): # decl is a basic type
            modifier_tail.type = decl
            return modifier
        else: # decl is a list of modifiers
            decl_tail = decl
            while not isinstance(decl_tail.type, VarDecl):
                decl_tail = decl_tail.type
            modifier_tail.type = decl_tail.type
            decl_tail.type = modifier_head
            return decl


    def _fix_decl_name_type(self, decl, typename):
        ''' Fixes a declaration. Modifies `decl`.\n
            Note: a type always has an underlying `VarDecl`, but it can be wrapped
            by modifiers, which are composed by `FuncDecl`, `ArrayDecl` and `PtrDecl`.
            This fixes the `Decl`'s `.name` to be equal to the `VarDecl`'s `.declname`.
        '''
        decl_tail = decl
        while not isinstance(decl_tail, VarDecl):
            decl_tail = decl_tail.type # reach the underlying basic type
        decl.name = decl_tail.declname # NOTE Decl.name and VarDecl.declname are of type ID

        if typename is None:
            if not isinstance(decl.type, FuncDecl):
                self._parse_error("Missing type in declaration", decl.coord)
            decl_tail.type = Type(['int'], coord=decl.coord) # NOTE functions return 'int' by default
        else:
            decl_tail.type = typename # NOTE this fixes the type=None passed to AST nodes

        return decl


    def _build_declaration(self, spec, decl, init=None):
        ''' Builds a declaration with the given specifier. '''
        return self._fix_decl_name_type(
            decl=Decl(None, decl, init, coord=decl.coord),
            typename=spec
        )


    def _build_declarations(self, spec, decls):
        ''' Builds a list of declarations all sharing the given specifiers.\n
            Note: `decls` is a list of dictionaries, mapping a declaration `decl`
            to its (optional) initialization `init` (i.e. `[dict(decl=.., init..),..]`).
        '''
        declarations = []
        for decl_with_init in decls:
            assert decl_with_init.get('decl') is not None
            declarations.append(
                self._build_declaration(
                    spec, # type specifier
                    decl_with_init['decl'], # declarator
                    decl_with_init.get('init') # optional initializer
                )
            )
        return declarations


    def _build_function_definition(self, spec, decl, param_decls, body):
        ''' Builds a function definition. '''
        declaration = self._build_declaration(spec, decl, init=None)
        return FuncDef(
            spec,
            declaration,
            param_decls,
            body,
            coord=decl.coord
        )


    # Grammar productions
    def p_error(self, p):
        if p is not None:
            print("Error near symbol '%s'" % p.value)
        else:
            print("Error at the end of input")


    def p_empty(self, p):
        ''' empty : '''
        p[0] = None


    def p_integer_constant(self, p):
        ''' integer_constant : INT_CONST '''
        p[0] = Constant("int", p[1], coord=self._token_coord(p, 1))


    def p_character_constant(self, p):
        ''' character_constant : CHAR_CONST '''
        p[0] = Constant("char", p[1], coord=self._token_coord(p, 1))


    def p_floating_constant(self, p):
        ''' floating_constant : FLOAT_CONST '''
        p[0] = Constant("float", p[1], coord=self._token_coord(p, 1))


    def p_string(self, p):
        ''' string : STRING_LITERAL '''
        p[0] = Constant("string", p[1], coord=self._token_coord(p, 1))


    def p_identifier(self, p):
        ''' identifier : ID '''
        p[0] = ID(p[1], coord=self._token_coord(p, 1))
        # TODO https://github.com/eliben/pycparser/blob/master/pycparser/c_parser.py#L1307
        # FIXME convert p_identifier__list into a p_identifier_list (separated by COMMA's)

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


    # NOTE top level rule
    def p_program(self, p):
        ''' program : global_declaration__list '''
        p[0] = Program(p[1])


    def p_global_declaration(self, p):
        ''' global_declaration : function_definition
                               | declaration
        '''
        if isinstance(p[1], FuncDef):
            p[0] = p[1] # NOTE FuncDef is not embedded into a GlobalDecl
        else: # Decl
            p[0] = GlobalDecl(p[1])

    def p_global_declaration__list(self, p):
        ''' global_declaration__list : global_declaration
                                     | global_declaration__list global_declaration
        '''
        p[0] = [p[1]] if len(p) == 2 else p[1] + [p[2]]


    def p_function_definition(self, p):
        ''' function_definition : type_specifier declarator declaration__list compound_statement
                                | type_specifier declarator       empty       compound_statement
                                |      empty     declarator declaration__list compound_statement
                                |      empty     declarator       empty       compound_statement
        '''
        if p[1] is not None:
            spec = p[1]
        else:
            spec = Type(['int'], coord=self._token_coord(p, 1)) # NOTE functions return 'int' by default

        p[0] = self._build_function_definition(
            spec,
            decl=p[2],
            param_decls=p[3], # FIXME this seems to always be None, so simply ignore it
            body=p[4]
        )


    def p_type_specifier(self, p):
        ''' type_specifier : VOID
                           | CHAR
                           | INT
                           | FLOAT
        '''
        p[0] = Type([p[1]], coord=self._token_coord(p, 1))


    def p_declarator(self, p):
        ''' declarator : pointer__opt direct_declarator '''
        if p[1] is None:
            p[0] = p[2]
        else:
            p[0] = self._type_modify_decl(p[2], p[1])


    def p_pointer(self, p):
        ''' pointer : TIMES pointer__opt %prec __DEREFERENCE '''
        # NOTE type=None later gets fixed by _fix_decl_name_type
        type_head = PtrDecl(None, coord=self._token_coord(p, 1))
        if p[2] is None:
            p[0] = type_head
        else:
            type_tail = p[2]
            while type_tail.type is not None:
                type_tail = type_tail.type
            type_tail.type = type_head
            p[0] = p[2]

    def p_pointer__opt(self, p):
        ''' pointer__opt : empty
                         | pointer
        '''
        p[0] = p[1]


    def p_direct_declarator(self, p):
        ''' direct_declarator : identifier
                              | LPAREN declarator RPAREN
                              | direct_declarator LBRACKET constant_expression__opt RBRACKET
                              | direct_declarator LPAREN parameter_list RPAREN
                              | direct_declarator LPAREN identifier__list__opt RPAREN
        '''
        # NOTE type=None later gets fixed by _fix_decl_name_type
        if len(p) == 2:
            p[0] = VarDecl(p[1], None, coord=self._token_coord(p, 1))
        elif len(p) == 4:
            p[0] = p[2]
        else:
            if p[2] == '[':
                array = ArrayDecl(None, p[3], coord=p[1].coord)
                p[0] = self._type_modify_decl(decl=p[1], modifier=array)
            else:
                func = FuncDecl(p[3], None, coord=p[1].coord)
                p[0] = self._type_modify_decl(decl=p[1], modifier=func)


    def p_constant_expression(self, p):
        ''' constant_expression : binary_expression '''
        p[0] = p[1]

    def p_constant_expression__opt(self, p):
        ''' constant_expression__opt : empty
                                     | constant_expression
        '''
        p[0] = p[1]


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
            p[0] = BinaryOp(p[2], p[1], p[3], coord=p[1].coord) # NOTE pass 'op' first


    def p_cast_expression(self, p):
        ''' cast_expression : unary_expression
                            | LPAREN type_specifier RPAREN cast_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = Cast(p[2], p[4], coord=self._token_coord(p, 1))


    def p_unary_expression(self, p):
        ''' unary_expression : postfix_expression
                             | PLUSPLUS unary_expression %prec __pre_PLUSPLUS
                             | MINUSMINUS unary_expression %prec __pre_MINUSMINUS
                             | unary_operator cast_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = UnaryOp(p[1], p[2], coord=p[2].coord)


    def p_postfix_expression(self, p):
        ''' postfix_expression : primary_expression
                               | postfix_expression LBRACKET expression RBRACKET
                               | postfix_expression LPAREN argument_expression_list__opt RPAREN
                               | postfix_expression PLUSPLUS %prec __post_PLUSPLUS
                               | postfix_expression MINUSMINUS %prec __post_MINUSMINUS
        '''
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 5:
            if p[2] == '[':
                p[0] = ArrayRef(p[1], p[3], coord=p[1].coord)
            else:
                p[0] = FuncCall(p[1], p[3], coord=p[1].coord)
        else:
            # NOTE a 'p' is added so we can differentiate this from when ++ or -- comes as a prefix
            p[0] = UnaryOp('p' + p[2], p[1], coord=p[1].coord) # NOTE pass 'op' first


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


    def p_constant(self, p):
        ''' constant : integer_constant
                     | character_constant
                     | floating_constant
        '''
        p[0]= p[1]


    def p_expression(self, p):
        ''' expression : assignment_expression
                       | expression COMMA assignment_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            if not isinstance(p[1], ExprList):
                p[1] = ExprList([p[1]], coord=p[1].coord)
            p[1].exprs.append(p[3])
            p[0] = p[1]

    def p_expression__opt(self, p):
        ''' expression__opt : empty
                            | expression
        '''
        p[0] = p[1]


    def p_argument_expression_list(self, p):
        ''' argument_expression_list : assignment_expression
                                     | argument_expression_list COMMA assignment_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            if not isinstance(p[1], ExprList):
                p[1] = ExprList([p[1]], coord=p[1].coord)
            p[1].exprs.append(p[3])
            p[0] = p[1]

    def p_argument_expression_list__opt(self, p):
        ''' argument_expression_list__opt : empty
                                          | argument_expression_list
        '''
        p[0] = p[1]


    def p_assignment_expression(self, p):
        ''' assignment_expression : binary_expression
                                  | unary_expression assignment_operator assignment_expression
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = Assignment(p[2], p[1], p[3], coord=p[1].coord) # NOTE pass 'op' first


    def p_assignment_operator(self, p):
        ''' assignment_operator : EQUALS
                                | TIMESEQUALS
                                | DIVEQUALS
                                | MODEQUALS
                                | PLUSEQUALS
                                | MINUSEQUALS
        '''
        p[0] = p[1]


    def p_unary_operator(self, p):
        ''' unary_operator : ADDRESS
                           | TIMES %prec __DEREFERENCE
                           | PLUS %prec __UPLUS
                           | MINUS %prec __UMINUS
                           | NOT
        '''
        p[0] = p[1]


    def p_parameter_list(self, p):
        ''' parameter_list : parameter_declaration
                           | parameter_list COMMA parameter_declaration
        '''
        if len(p) == 2:
            p[0] = ParamList([p[1]], coord=p[1].coord)
        else:
            p[1].params.append(p[3])
            p[0] = p[1]


    def p_parameter_declaration(self, p):
        ''' parameter_declaration : type_specifier declarator '''
        p[0] = self._build_declaration(spec=p[1], decl=p[2], init=None)


    def p_declaration(self, p):
        ''' declaration : type_specifier init_declarator_list__opt SEMI '''
        if p[2] is None:
            # FIXME this will lead to an assertion error
            p[0] = self._build_declarations(spec=p[1], decls=[dict(decl=None, init=None)])
        else:
            p[0] = self._build_declarations(spec=p[1], decls=p[2])

    def p_declaration__list__opt(self, p):
        ''' declaration__list__opt : empty
                                   | declaration__list
        '''
        p[0] = p[1]

    def p_declaration__list(self, p):
        ''' declaration__list : declaration
                              | declaration__list declaration
        '''
        p[0] = p[1] if len(p) == 2 else p[1] + p[2] # NOTE declaration is already a list


    def p_init_declarator_list(self, p):
        ''' init_declarator_list : init_declarator
                                 | init_declarator_list COMMA init_declarator
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_init_declarator_list__opt(self, p):
        ''' init_declarator_list__opt : empty
                                      | init_declarator_list
        '''
        p[0] = p[1]


    def p_init_declarator(self, p):
        ''' init_declarator : declarator
                            | declarator EQUALS initializer
        '''
        if len(p) == 2:
            p[0] = dict(decl=p[1], init=None)
        else:
            p[0] = dict(decl=p[1], init=p[3])


    def p_initializer(self, p):
        ''' initializer : assignment_expression
                        | LBRACE initializer_list RBRACE
                        | LBRACE initializer_list COMMA RBRACE
        '''
        if len(p) == 2:
            p[0] = p[1]
        else:
            p[0] = p[2] # FIXME should the initializer_list be __opt (?)


    def p_initializer_list(self, p):
        ''' initializer_list : initializer
                             | initializer_list COMMA initializer
        '''
        if len(p) == 2:
            p[0] = InitList([p[1]], coord=p[1].coord)
        else:
            if not isinstance(p[1], InitList):
                p[1] = InitList([p[1]], coord=p[1].coord)
            p[1].exprs.append(p[3])
            p[0] = p[1]


    def p_compound_statement(self, p):
        ''' compound_statement : LBRACE declaration__list__opt statement__list__opt RBRACE '''
        coord = self._token_coord(p, 1)
        coord.column = 1 # FIXME this is a hack to match the expected coord value
        p[0] = Compound(p[2], p[3], coord=coord)


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


    def p_expression_statement(self, p):
        ''' expression_statement : expression__opt SEMI '''
        if p[1] is None:
            p[0] = EmptyStatement(coord=self._token_coord(p, 2))
        else:
            p[0] = p[1]


    def p_selection_statement(self, p):
        ''' selection_statement : IF LPAREN expression RPAREN statement
                                | IF LPAREN expression RPAREN statement ELSE statement
        '''
        if len(p) == 6:
            p[0] = If(p[3], p[5], None, coord=self._token_coord(p, 1))
        else:
            p[0] = If(p[3], p[5], p[7], coord=self._token_coord(p, 1))


    def p_iteration_statement(self, p):
        ''' iteration_statement : WHILE LPAREN expression RPAREN statement
                                | FOR LPAREN expression__opt SEMI expression__opt SEMI expression__opt RPAREN statement
                                | FOR LPAREN declaration expression__opt SEMI expression__opt RPAREN statement
        '''
        if len(p) == 6:
            p[0] = While(p[3], p[5], coord=self._token_coord(p, 1))
        elif len(p) == 10:
            p[0] = For(p[3], p[5], p[7], p[9], coord=self._token_coord(p, 1))
        else:
            p[0] = For(DeclList(p[3], coord=self._token_coord(p, 1)), p[4], p[6], p[8], coord=self._token_coord(p, 1))


    def p_jump_statement(self, p):
        ''' jump_statement : BREAK SEMI
                           | RETURN expression__opt SEMI
        '''
        if len(p) == 3:
            p[0] = Break(coord=self._token_coord(p, 1))
        else:
            p[0] = Return(p[2], coord=self._token_coord(p, 1))


    def p_assert_statement(self, p):
        ''' assert_statement : ASSERT expression SEMI '''
        p[0] = Assert(p[2], coord=self._token_coord(p, 1))


    def p_print_statement(self, p):
        ''' print_statement : PRINT LPAREN argument_expression_list__opt RPAREN SEMI '''
        p[0] = Print(p[3], coord=self._token_coord(p, 1))


    def p_read_statement(self, p):
        ''' read_statement : READ LPAREN argument_expression_list RPAREN SEMI '''
        p[0] = Read(p[3], coord=self._token_coord(p, 1))


class Coord:
    ''' Coordinates of a syntactic element.\n
        Consists of:
        - `line`: Line number.
        - `column`: Column number, for the Lexer (optional).
    '''
    __slots__ = ('line', 'column', '__weakref__')

    def __init__(self, line, column=None):
        self.line = line
        self.column = column

    def __str__(self):
        if self.line:
            return "   @ %s:%s" % (self.line, self.column)
        return ""
