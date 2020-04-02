import re

from ply.lex import LexToken

from uC_parser import UCParser

###########################################################
## misc ###################################################
###########################################################

m = UCParser()

examples = [
    "int* c[5];",

    "int a = 3 * 4 + 5;",

    "int x, y, z = 5;",

    "int c[5];",

    "float b = 2.;",

    '\n'.join([
        "int a;",
        "a = 3 * 4 + 5;",
        "print (a);"
    ]),

    '\n'.join([
        "int x = 10;",
        "int main () {",
        "  int z = 5;",
        "  int y;",
        "  read(y);",
        "  print(x * (y + z));",
        "  return;",
        "}",
    ]),

    '\n'.join([
        "/* comment */",
        "int j = 3;",
        "int main () {",
        "  int i = j;",
        "  int k = 3;",
        "  int p = 2 * j;",
        "  assert p == 2 * i;",
        "}",
    ])
]

###########################################################
## tests ##################################################
###########################################################

# FIXME create tests for pytest

if __name__ == "__main__":
    print(m.parse(examples[0]))
    print()
    print(m.parse(examples[1]))