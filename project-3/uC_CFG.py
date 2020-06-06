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
    def extract_from(instr_tuple):
        head, *tail = instr_tuple

        if head.startswith("alloc"):
            return Instruction.Type.ALLOC

        elif head.startswith("global"):
            return Instruction.Type.GLOBAL

        elif head.startswith("load"):
            return Instruction.Type.LOAD

        elif head.startswith("store"):
            return Instruction.Type.STORE

        elif head.startswith("literal"):
            return Instruction.Type.LITERAL

        elif head.startswith("elem"):
            return Instruction.Type.ELEM

        elif head.startswith("fptosi"):
            return Instruction.Type.FPTOSI

        elif head.startswith("sitofp"):
            return Instruction.Type.SITOFP

        elif head.startswith("jump"):
            return Instruction.Type.JUMP

        elif head.startswith("cbranch"):
            return Instruction.Type.CBRANCH

        elif head.startswith("define"):
            return Instruction.Type.DEFINE

        elif head.startswith("call"):
            return Instruction.Type.CALL

        elif head.startswith("return"):
            return Instruction.Type.RETURN

        elif head.startswith("param"):
            return Instruction.Type.PARAM

        elif head.startswith("read"):
            return Instruction.Type.READ

        elif head.startswith("print"):
            return Instruction.Type.PRINT

        elif head in Instruction.opcode.values():
            return Instruction.Type.OP

        else:
            return Instruction.Type.LABEL


class ControlFlowGraph:
    ''' Control-flow graph (CFG) representation of a uC program. '''

    def __init__(self, ircode):
        # TODO create basic blocks from the IR
        pp = []

        leader_to_line = { '$head': 0 }
        branch_targets = set()

        for i, code_instr in enumerate(ircode):
            instr_type = Instruction.extract_from(code_instr)
            if instr_type == Instruction.Type.DEFINE:
                _, source = code_instr
                leader_to_line[source] = i
            elif instr_type == Instruction.Type.JUMP:
                # NOTE i+1 is a leader
                _, target = code_instr
                branch_targets.add(target)
            elif instr_type == Instruction.Type.CBRANCH:
                # NOTE i+1 is a leader
                _, _, true_target, false_target = code_instr
                branch_targets.add(true_target)
                branch_targets.add(false_target)
            pp.append(Instruction.extract_from(code_instr).name.rjust(8) + "=>" + str(code_instr))


        # NOTE make instructions subject to deviation leaders
        for i, code_instr in enumerate(ircode):
            instr_type = Instruction.extract_from(code_instr)
            if instr_type == Instruction.Type.LABEL:
                label = f"%{code_instr[0]}"
                if label in branch_targets:
                    leader_to_line[label] = i

        print(leader_to_line)

        # make blocks from leaders starting lines
        line_to_leader = {v: k for k, v in leader_to_line.items()}
        leader_lines = list(sorted(line_to_leader.keys()))
        leader_lines.append(len(ircode)) # accounts for last block creation
        leaders = {}

        for start, end in zip(leader_lines[:-1], leader_lines[1:]):
            label = line_to_leader[start]
            leaders[label] = Block(label)
            leaders[label].extend(ircode[start:end])
            # print(f"{start=}, {end-1=} {leaders[label]=}")


        for (label, block), next_line in zip(leaders.items(), leader_lines[1:]):
            if next_line == len(ircode): break

            last_instr = block.instructions[-1]
            instr_type = Instruction.extract_from(last_instr)

            if instr_type == Instruction.Type.JUMP:
                _, target = last_instr
                block.next_block[True] = leaders[target]

            elif instr_type == Instruction.Type.CBRANCH:
                _, _, true_target, false_target = last_instr
                block.next_block[True] = leaders[true_target]
                block.next_block[False] = leaders[false_target]

            else:
                block.next_block[True] = leaders[line_to_leader[next_line]]

        for i, p in enumerate(pp):
            print(str(i).rjust(2), ":  " if i not in line_to_leader else ": *", p)
        
        print(leaders)
