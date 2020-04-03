import weakref

from _uC_AST import *
from uC_parser import Coord

###########################################################
## tests ##################################################
###########################################################

def test_BinaryOp():
    b1 = BinaryOp(
        op='+',
        left=Constant(type='int', value='6'),
        right=ID(name='joe')
    )

    assert isinstance(b1.left, Constant)
    assert b1.left.type =='int'
    assert b1.left.value =='6'

    assert isinstance(b1.right, ID)
    assert b1.right.name =='joe'

def test_weakref_works_on_nodes():
    c1 = Constant(type='float', value='3.14')
    wr = weakref.ref(c1)
    cref = wr()
    assert cref.type == 'float'
    assert weakref.getweakrefcount(c1) == 1

def test_weakref_works_on_coord():
    coord = Coord(line=2)
    wr = weakref.ref(coord)
    cref = wr()
    assert cref.line == 2
    assert weakref.getweakrefcount(coord) == 1

# TODO test NodeVisitor

# ref.: https://github.com/eliben/pycparser/blob/master/tests/test_c_ast.py
