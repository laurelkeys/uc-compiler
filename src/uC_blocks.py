from collections import namedtuple

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

In_Out = namedtuple(typename="In_Out", field_names=["in_", "out"])
Gen_Kill = namedtuple(typename="Gen_Kill", field_names=["gen", "kill"])

class Block:
    ''' Base class representing a CFG block. '''

    def __init__(self, label=None):
        self.label = label      # label that identifies the block
        self.instructions = []  # instructions in the block
        self.successors = []    # list of successors
        self.predecessors = []  # list of predecessors

        self.in_out = In_Out(set(), set())
        self.gen_kill = Gen_Kill(set(), set())

        self.in_out_per_line = []
        self.gen_kill_per_line = []

    def append(self, instr):
        self.instructions.append(instr)

    def extend(self, instr_list):
        self.instructions.extend(instr_list)

    def __iter__(self):
        return iter(self.instructions)

    def __repr__(self):
        return (
            f"Block({self.label}"
            + f", successors=[{', '.join([s.label for s in self.successors])}]"
            + f", predecessors=[{', '.join([p.label for p in self.predecessors])}]"
            + ")"
        )
