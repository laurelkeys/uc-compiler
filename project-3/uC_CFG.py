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
        pp = []

        leader_lines = { 0 }
        leader_to_line = { f"$first": 0 }
        branch_targets = set()

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
            pp.append(Instruction.type_of(code_instr).name.rjust(8) + "=>" + str(code_instr))

        # NOTE make instructions subject to deviation leaders
        for i, code_instr in enumerate(ircode):
            if Instruction.type_of(code_instr) == Instruction.Type.LABEL:
                label = f"%{code_instr[0]}"
                if label in branch_targets:
                    leader_lines.add(i)
                    leader_to_line[label] = i

        # create blocks from leaders' starting lines
        line_to_leader = { v: k for k, v in leader_to_line.items() }
        assert set(line_to_leader.keys()) == leader_lines
        leader_lines = list(sorted(leader_lines))

        leaders = {}
        for start, end in zip(leader_lines, leader_lines[1:] + [len(ircode)]):
            label = line_to_leader[start]
            leaders[label] = Block(label)
            leaders[label].extend(ircode[start:end])

        for (label, block), next_leader_line in zip(leaders.items(), leader_lines[1:]):
            last_instr = block.instructions[-1]
            instr_type = Instruction.type_of(last_instr)

            if instr_type == Instruction.Type.JUMP:
                _, target = last_instr
                block.sucessors.append(leaders[target])

            elif instr_type == Instruction.Type.CBRANCH:
                _, _, true_target, false_target = last_instr
                block.sucessors.append(leaders[true_target])
                block.sucessors.append(leaders[false_target])

            else:
                block.sucessors.append(leaders[line_to_leader[next_leader_line]])

        for i, p in enumerate(pp):
            print(str(i).rjust(2), ":  " if i not in line_to_leader else ": *", p)

        print("\n" + "\n".join(map(str, leaders.values())))

        print(leader_to_line)
        print(line_to_leader)
