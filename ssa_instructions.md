# SSA code instructions
Your SSA ([Static Single Assignment](https://en.wikipedia.org/wiki/Static_single_assignment_form)) code should only contain the following operators, represented as tuples of the form `(operation, operands, ..., destination)`:

## Variables & Values:
```python
       ('alloc_type', varname)                  # Allocate on stack (ref by register) a variable of a given type
       ('global_type', varname, value)          # Allocate on heap a global var of a given type. value is optional
       ('load_type', varname, target)           # Load the value of a variable (stack/heap) into target (register)
       ('store_type', source, target)           # Store the source/register into target/varname
       ('literal_type', value, target)          # Load a literal value into target
       ('elem_type', source, index, target)     # Load into target the address of source (array) indexed by index
```
## Binary Operations:
```python
       ('add_type', left, right, target)    # target = left + right
       ('sub_type', left, right, target)    # target = left - right
       ('mul_type', left, right, target)    # target = left * right
       ('div_type', left, right, target)    # target = left / right  (integer truncation)
       ('mod_type', left, right, target)    # target = left % right
```
## Cast Operations:
```python
       ('fptosi', fvalue, target)           # target = (int)fvalue == cast float to int
       ('sitofp', ivalue, target)           # target = (float)ivalue == cast int to float
```
## Relational/Equality/Logical:
```python
       (`oper`_type, left, right, target)   # target = left `oper` right, where `oper` is:
                                            #          lt, le, ge, gt, eq, ne, and, or
```
## Labels & Branches:
```python
       ('label:', )                                         # Label definition
       ('jump', target)                                     # Jump to a target label
       ('cbranch', expr_test, true_target, false_target)    # Conditional branch
```
## Functions & Built-ins:
```python
       ('define', source)               # Function definition. `source` is a function label
       ('end', )                        # End of a function definition
       ('call', source, target)         # Call a function. `target` is an optional return value
       ('return_type', target)          # Return from function. `target` is an optional return value
       ('param_type', source)           # `source` is an actual parameter
       ('read_type', source)            # Read value to `source`
       ('print_type', source)           # Print value of `source`
```

## A note about arrays:
The dimensions of an array in uC are known at compile time. Thus, the type described in the allocation must express the dimension of the same. The `initializer_list` are always allocated in the heap, either directly in the declaration of the variable, if it is global, or by defining a new temporary, based on the name of the local variable.

## A note about pointers:
The allocation and operations with pointers in uC follow the same structure used for arrays. The exception is that reading the referenced value requires two instructions.
