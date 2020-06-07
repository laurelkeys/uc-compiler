from enum import Enum, unique

from uC_blocks import *

###########################################################
## uC Control-Flow Graph (CFG) ############################
###########################################################


class Instruction:
    opcode = {
        '+':  'add', '-':  'sub',
        '*':  'mul', '/':  'div', '%': 'mod',

        '&&': 'and', '||': 'or',

        '==': 'eq',  '!=': 'ne',
        '<':  'lt',  '<=': 'le',
        '>':  'gt',  '>=': 'ge',
    }

    @unique
    class Type(Enum):
        ALLOC   =  1  # _type, varname
        GLOBAL  =  2  # _type, varname, opt_value=None
        LOAD    =  3  # _type, varname, target
        STORE   =  4  # _type, source, target
        LITERAL =  5  # _type, value, target
        ELEM    =  6  # _type, source, index, target
        FPTOSI  =  7  # fvalue, target
        SITOFP  =  8  # ivalue, target
        OP      =  9  # _op, _type, left, right, target
        LABEL   = 10  # label
        JUMP    = 11  # target
        CBRANCH = 12  # expr_test, true_target, false_target
        DEFINE  = 13  # source
        CALL    = 14  # source, opt_target=None):
        RETURN  = 15  # _type, opt_target=None
        PARAM   = 16  # _type, source
        READ    = 17  # _type, source
        PRINT   = 18  # _type, source=None

    @staticmethod
    def type_of(instr_tuple):
        head, *_ = instr_tuple

        if head in Instruction.opcode.values():
            return Instruction.Type.OP

        # HACK this relies on names not overlapping
        for instr_type in Instruction.Type:
            if head.startswith(instr_type.name.lower()):
                return instr_type

        return Instruction.Type.LABEL


class ControlFlowGraph:
    ''' Control-flow graph (CFG) representation of a uC program. '''

    def __init__(self, ircode):
        ''' Represent the IR code as a graph of basic blocks. '''
        self.entries = {}

        leader_lines = set()
        leader_to_line = dict()
        branch_targets = set()

        # FIXME treat global variable declarations

        # make defines and instructions following deviations leaders
        for i, code_instr in enumerate(ircode):
            instr_type = Instruction.type_of(code_instr)
            if instr_type == Instruction.Type.DEFINE:
                leader_lines.add(i)
                _, source = code_instr
                leader_to_line[source] = i
            elif instr_type == Instruction.Type.JUMP:
                leader_lines.add(i + 1)
                _, target = code_instr
                branch_targets.add(target)
            elif instr_type == Instruction.Type.CBRANCH:
                leader_lines.add(i + 1)
                _, _, true_target, false_target = code_instr
                branch_targets.add(true_target)
                branch_targets.add(false_target)

        # make instructions subject to deviation leaders
        for i, code_instr in enumerate(ircode):
            if Instruction.type_of(code_instr) == Instruction.Type.LABEL:
                label = f"%{code_instr[0]}"
                if label in branch_targets:
                    leader_lines.add(i)
                    leader_to_line[label] = i

        assert set(leader_to_line.values()) == leader_lines  # sanity check
        leader_lines = list(sorted(leader_lines))

        # create blocks from leaders' starting lines
        line_to_leader = { v: k for k, v in leader_to_line.items() }
        leaders = {}

        for start, end in zip(leader_lines, leader_lines[1:] + [len(ircode)]):
            label = line_to_leader[start]
            if label[0] == "@":
                leaders[label] = Block("entry")
                leaders[label].extend(ircode[start + 1:end])
                self.entries[label] = leaders[label]
            else:
                leaders[label] = Block(label)
                leaders[label].extend(ircode[start:end])

        # connect blocks that belong to the same function
        for (label, block), next_leader_line in zip(leaders.items(), leader_lines[1:]):
            last_instr = block.instructions[-1]
            instr_type = Instruction.type_of(last_instr)

            if instr_type == Instruction.Type.JUMP:
                _, target = last_instr
                block.sucessors.append(leaders[target])
                leaders[target].predecessors.append(block)

            elif instr_type == Instruction.Type.CBRANCH:
                _, _, true_target, false_target = last_instr
                block.sucessors.append(leaders[true_target])
                block.sucessors.append(leaders[false_target])
                leaders[true_target].predecessors.append(block)
                leaders[false_target].predecessors.append(block)

            elif instr_type != Instruction.Type.RETURN:
                next_leader_label = line_to_leader[next_leader_line]
                block.sucessors.append(leaders[next_leader_label])
                leaders[next_leader_label].predecessors.append(block)

        print("\n" + "\n".join(map(str, leaders.values())))

        print(leader_to_line)
        print(line_to_leader)
