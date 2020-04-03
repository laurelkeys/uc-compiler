```
<program> ::= {<global_declaration>}+

<global_declaration> ::= <function_definition>
                       | <declaration>

<function_definition> ::= {<type_specifier>}? <declarator> {<declaration>}* <compound_statement>

<type_specifier> ::= void
                   | char
                   | int
                   | float

<declarator> ::= {<pointer>}? <direct_declarator>

<pointer> ::= * {<pointer>}?

<direct_declarator> ::= <identifier>
                      | ( <declarator> )
                      | <direct_declarator> [ {<constant_expression>}? ]
                      | <direct_declarator> ( <parameter_list> )
                      | <direct_declarator> ( {<identifier>}* )

<constant_expression> ::= <binary_expression>

<binary_expression> ::= <cast_expression>
                      | <binary_expression> * <binary_expression>
                      | <binary_expression> / <binary_expression>
                      | <binary_expression> % <binary_expression>
                      | <binary_expression> + <binary_expression>
                      | <binary_expression> - <binary_expression>
                      | <binary_expression> < <binary_expression>
                      | <binary_expression> <= <binary_expression>
                      | <binary_expression> > <binary_expression>
                      | <binary_expression> >= <binary_expression>
                      | <binary_expression> == <binary_expression>
                      | <binary_expression> != <binary_expression>
                      | <binary_expression> && <binary_expression>
                      | <binary_expression> || <binary_expression>

<cast_expression> ::= <unary_expression>
                    | ( <type_specifier> ) <cast_expression>

<unary_expression> ::= <postfix_expression>
                     | ++ <unary_expression>
                     | -- <unary_expression>
                     | <unary_operator> <cast_expression>

<postfix_expression> ::= <primary_expression>
                       | <postfix_expression> [ <expression> ]
                       | <postfix_expression> ( {<argument_expression_list>}? )
                       | <postfix_expression> ++
                       | <postfix_expression> --

<primary_expression> ::= <identifier>
                       | <constant>
                       | <string>
                       | ( <expression> )

<constant> ::= <integer_constant>
             | <character_constant>
             | <floating_constant>

<expression> ::= <assignment_expression>
               | <expression> , <assignment_expression>

<argument_expression_list> ::= <assignment_expression>
                             | <argument_expression_list> , <assignment_expression>

<assignment_expression> ::= <binary_expression>
                          | <unary_expression> <assignment_operator> <assignment_expression>

<assignment_operator> ::= =
                        | *=
                        | /=
                        | %=
                        | +=
                        | -=

<unary_operator> ::= &
                   | *
                   | +
                   | -
                   | !

<parameter_list> ::= <parameter_declaration>
                   | <parameter_list> , <parameter_declaration>

<parameter_declaration> ::= <type_specifier> <declarator>

<declaration> ::=  <type_specifier> {<init_declarator_list>}? ;

<init_declarator_list> ::= <init_declarator>
                         | <init_declarator_list> , <init_declarator>

<init_declarator> ::= <declarator>
                    | <declarator> = <initializer>

<initializer> ::= <assignment_expression>
                | { <initializer_list> }
                | { <initializer_list> , }

<initializer_list> ::= <initializer>
                     | <initializer_list> , <initializer>

<compound_statement> ::= { {<declaration>}* {<statement>}* }

<statement> ::= <expression_statement>
              | <compound_statement>
              | <selection_statement>
              | <iteration_statement>
              | <jump_statement>
              | <assert_statement>
              | <print_statement>
              | <read_statement>

<expression_statement> ::= {<expression>}? ;

<selection_statement> ::= if ( <expression> ) <statement>
                        | if ( <expression> ) <statement> else <statement>

<iteration_statement> ::= while ( <expression> ) <statement>
                        | for ( {<expression>}? ; {<expression>}? ; {<expression>}? ) <statement>
                        | for ( <declaration> {<expression>}? ; {<expression>}? ) <statement>

<jump_statement> ::= break ;
                   | return {<expression>}? ;

<assert_statement> ::= assert <expression> ;

<print_statement> ::= print ( {<argument_expression_list>}? ) ;

<read_statement> ::= read ( <argument_expression_list> ) ;
```