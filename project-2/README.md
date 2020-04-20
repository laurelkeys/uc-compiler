- [Sematic Rules](#sematic-rules)
  - [Names and symbols](#names-and-symbols)
  - [Types of literals](#types-of-literals)
  - [Binary operator type checking](#binary-operator-type-checking)
  - [Unary operator type checking](#unary-operator-type-checking)
  - [Supported operators](#supported-operators)
  - [Assignment, indexing, etc.](#assignment-indexing-etc)
- [SSA code instructions](#ssa-code-instructions)
  - [Variables & Values:](#variables--values)
  - [Binary Operations:](#binary-operations)
  - [Unary Operations:](#unary-operations)
  - [Relational/Equality/Logical:](#relationalequalitylogical)
  - [Labels & Branches:](#labels--branches)
  - [Functions & Builtins:](#functions--builtins)

# Sematic Rules

## Names and symbols
All identifiers must be defined before they are used. This includes variables and functions. For example, this kind of code generates an error:
```c
   a = 3;       // Error:  'a' not defined
   int a;
```
**Note:** typenames such as `"int"`, `"float"`, and `"char"` are built-in names that should be defined at the start of the program.

## Types of literals
All literal symbols must be assigned a type of `"int"`, `"float"`, `"char"` or `"string"`.
For example:
```c
    42;         // Type "int"
    4.2;        // Type "float"
    'x';        // Type "char"
    "forty";    // Type "string"
```
To do this assignment, check the Python type of the literal value and attach a type name as appropriate.

## Binary operator type checking
Binary operators only operate on operands of the same type and produce a result of the same type. Otherwise, you get a type error. For example:
```c
    int a = 2;
    float b = 3.14;

    int c = a + 3;      // OK
    int d = a + b;      // Error:  int + float
    int e = b + 4.5;    // Error:  int = float
```

## Unary operator type checking
Unary operators return a result that's the same type as the operand.

## Supported operators
Attempts to use unsupported operators should result in an error. For example:
```c
    char[] a = "Hello" + "World";   // OK
    char[] b = "Hello" * "World";   // Error:  unsupported op *
```

## Assignment, indexing, etc.
The left- and right-hand sides of an assignment operation must be declared as the same type. The size of objects must match. The index of an array must be of type int. Etc. See the examples below:
```c
int v[4] = {1, 2, 3};   // Error:  size mismatch on initialization
float f;
int j = v[f];           // Error:  array index must be of type int
j = f;                  // Error:  cannot assign float to int
```
However, string literals can be assigned to array of chars. See the example below:
```c
char c[] = "Susy";      // Ok
```
In this case, the size of `c` must be inferred from the initialization.

# SSA code instructions
Your SSA ([Static Single Assignment](https://en.wikipedia.org/wiki/Static_single_assignment_form)) code should only contain the following operators:

## Variables & Values:
```python
       ('alloc_type', varname)          # Allocate on stack (ref by register) a variable of a given type
       ('global_type', varname, value)  # Allocate on heap a global var of a given type. value is optional
       ('load_type', varname, target)   # Load the value of a variable (stack or heap) into target (register)
       ('store_type', source, target)   # Store the source/register into target/varname
       ('literal_type', value, target)  # Load a literal value into target
```
## Binary Operations:
```python
       ('add_type', left, right, target )   # target = left + right
       ('sub_type', left, right, target)    # target = left - right
       ('mul_type', left, right, target)    # target = left * right
       ('div_type', left, right, target)    # target = left / right  (integer truncation)
       ('mod_type', left, right, target)    # target = left % rigth
```
## Unary Operations:
```python
       ('uadd_type', source, target)        # target = +source
       ('uneg_type', source, target)        # target = -source
```
## Relational/Equality/Logical:
```python
       (`oper`, left, right, target)    # target = left `oper` rigth, where `oper` is:
                                        #          lt, le, ge, gt, eq, ne, and, or
```
## Labels & Branches:
```python
       ('label', )                                          # Label definition
       ('jump', target)                                     # Jump to a target label
       ('cbranch', expr_test, true_target, false_target)    # Conditional branch
```
## Functions & Builtins:
```python
       ('define', source)               # Function definition. `source` is a function label 
       ('end', )                        # End of a function definition
       ('call', source, target)         # Call a function. `target` is an optional return value
       ('return_type', source, target)  # Return from function. `target` is an optional return value
       ('param_type', source)           # `source` is an actual parameter
       ('read_type', source)            # Read value to `source`
       ('print_type',source)            # Print value of `source`