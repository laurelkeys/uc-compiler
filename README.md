# uc-compiler
A compiler for the [μC programming language](https://github.com/iviarcio/mc921/blob/master/uC_Grammar.ipynb), developed during Unicamp's Compiler Design and Construction course ([MC921](https://guidoaraujo.wordpress.com/mc921ab/)).

See the [BNF grammar specification](bnf_grammar.md) and the [semantic rules](semantic_rules.md) of the language.

## Usage
```
$ python src\uC.py -h
usage: uC.py [-h] [-s] [-a] [-i] [-o] [-l]
             [-p {ctm,dce,cfg,all}] [-n] [-c] [-d]
             filename

uC (micro C) language compiler

positional arguments:
  filename              path to a .uc file to compile

optional arguments:
  -h, --help            show this help message and exit
  -s, --susy            run in the susy machine
  -a, --ast             dump the AST to <filename>.ast
  -i, --ir              dump the uCIR to <filename>.ir
  -o, --opt             optimize the uCIR and dump it to <filename>.opt
  -l, --llvm            generate LLVM IR code and dump it to <filename>.ll
  -p {ctm,dce,cfg,all}, --llvm-opt {ctm,dce,cfg,all}
                        specify which LLVM pass optimizations to enable
  -n, --no-run          do not execute the program
  -c, --cfg             show the CFG for each function in png format
  -d, --debug           print debug information
```
