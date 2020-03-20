import re
import ply.yacc as yacc

from uC_lexer import UCLexer
from uC_AST import Program, \
                   ID

# NOTE Yacc uses a parsing technique known as LR-parsing or shift-reduce parsing.
#      LR parsing is a bottom up technique that tries to recognize the right-hand-side of various grammar rules.
#      Whenever a valid right-hand-side is found in the input, the appropriate action code is triggered and the
#      grammar symbols are replaced by the grammar symbol on the left-hand-side.

# NOTE Each rule is defined by a function whose docstring contains the appropriate context-free grammar specification.
#      The statements that make up the function body implement the semantic actions of the rule.
#      Each function accepts a single argument `p` that is a sequence containing the values of each grammar symbol
#      in the corresponding rule. The values of `p[i]` are mapped to grammar symbols, in order.

# NOTE The use of negative indices have a special meaning in yacc, thus, do not use them (e.g. p[-1])

###########################################################
## uC Parser ##############################################
###########################################################

class UCParser:
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

    def p_declaration_list_opt(self, p):
      ''' declaration_list_opt : empty
                               | declaration_list
      '''
      p[0] = p[1]

    def p_empty(self, p):
        ''' empty : '''
        p[0] = None

    def p_error(self, p):
        if p is not None:
            print("Error near symbol '%s'" % p.value)
        else:
            print("Error at the end of input")