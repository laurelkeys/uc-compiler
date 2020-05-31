import os
import sys

from collections import ChainMap

import uC_ops
import uC_types

from uC_AST import *

from uC_types import (TYPE_INT, TYPE_FLOAT, TYPE_CHAR, TYPE_STRING, TYPE_VOID,
                      TYPE_BOOL, TYPE_ARRAY, TYPE_FUNC)

# NOTE A basic block (BB) is a sequence of instructions where the control flow enters
#      only at the beginning of the block and exits at the end of the block, without the
#      possibility of deviation to any other part of the program.

# NOTE The set of basic block leaders are defined as:
#      1. The first instruction is a leader;
#      2. Any instruction that is subject to conditional or unconditional deviation is a leader;
#      3. Any instruction that comes immediately after a conditional or unconditional deviation instruction is a leader;
#      4. For each leader, your basic block consists of the leader and all instructions that follow him to the next leader, excluding this last.

# NOTE The first statement in a BB is always a label and the last statement is a jump statement (conditional or unconditional).

# NOTE Function calls are not treated as branches, their successor is the instruction immediately after the call.
#      Return nodes do not have any successors.

# NOTE Unconditional jumps have only one successor: the target of the jump statement.
#      When you see an unconditional jump, add the target of the jump statement as a successor of the jump,
#      and the jump statement as a predecessor of the target.

# NOTE Conditional jumps have two successors: the `fall_through` target, which can be a successor in the linked list, and the `taken` target.
#      Add the branch as a predecessor of the taken target, and the taken target as an additional successor of the branch.

###########################################################
## uC Basic Blocks (BBs) ##################################
###########################################################

class Block:
    ''' Base class representing a CFG block. '''

    def __init__(self, label):
        self.label = label      # label that identifies the block
        self.instructions = []  # instructions in the block
        self.sucessors = []     # list of sucessors
        self.predecessors = []  # list of predecessors
        self.next_block = None  # link to the next block

        if label is not None:
            self.instructions.append((label, ))  # FIXME use emit_label

    def append(self,instr):
        self.instructions.append(instr)

    def __iter__(self):
        return iter(self.instructions)

class BasicBlock(Block):
    ''' Class for a simple basic block.\n
        Control flow unconditionally flows to the next block.
    '''

    def __init__(self, label):
        super(BasicBlock, self).__init__(label)

class ConditionBlock(Block):
    ''' Class for a block representing an conditional statement.\n
        There are two branches to handle each possibility.
    '''

    def __init__(self, label):
        super(ConditionBlock, self).__init__(label)
        self.taken = None
        self.fall_through = None

class BlockVisitor:
    ''' Class for visiting basic blocks.\n
        Define a subclass and methods such as `visit_BasicBlock()` or `visit_ConditionBlock()`
        to implement custom processing (similar to AST's `NodeVisitor`).
    '''

    def visit(self, block):
        while isinstance(block, Block):
            name = "visit_%s" % type(block).__name__
            if hasattr(self, name):
                getattr(self, name)(block)
            block = block.next_block

class EmitBlocks(BlockVisitor):
    ''' Block visitor class that creates basic blocks for the CFG. '''

    def __init__(self):
        self.code = []

    def visit_BasicBlock(self, block: BasicBlock):
        self.code.extend(block.instructions)

    def visit_ConditionBlock(self, block: ConditionBlock):
        self.code.extend(block.instructions)
