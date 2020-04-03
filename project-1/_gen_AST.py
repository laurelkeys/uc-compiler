if __name__ == "__main__":
    from _ast_gen import ASTCodeGenerator
    ast_gen = ASTCodeGenerator('_uC_AST.cfg')
    ast_gen.generate(open('_uC_AST.py', 'w'))