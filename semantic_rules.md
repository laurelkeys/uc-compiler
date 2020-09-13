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
    char a[] = "Hello" + "World";   // OK
    char b[] = "Hello" * "World";   // Error:  unsupported op *
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
