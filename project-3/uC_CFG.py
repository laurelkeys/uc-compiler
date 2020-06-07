from collections import namedtuple
from enum import Enum, unique

from uC_blocks import *
from uC_IR import Instruction

###########################################################
## uC Control-Flow Graph (CFG) ############################
###########################################################


class ControlFlowGraph:
    ''' Control-flow graph (CFG) representation of a uC program. '''

    def __init__(self, ircode):
        ''' Represent the IR code as a graph of basic blocks. '''
        self.entries = {}

        leader_lines = set()
        entry_exit_line = {}
        entry_branch_targets = {}
        entry_leaders_to_lines = {}
        # FIXME treat global variable declarations

        # make defines and instructions following deviations leaders
        curr_entry = None
        for i, code_instr in enumerate(ircode):
            instr_type = Instruction.type_of(code_instr)

            if instr_type == Instruction.Type.DEFINE:
                leader_lines.add(i)
                if curr_entry is not None:
                    entry_exit_line[curr_entry] = i - 1
                curr_entry = code_instr[1]
                entry_branch_targets[curr_entry] = set()
                entry_leaders_to_lines[curr_entry] = {"entry": i}

            elif instr_type == Instruction.Type.JUMP:
                leader_lines.add(i + 1)
                _, target = code_instr
                entry_branch_targets[curr_entry].add(target)

            elif instr_type == Instruction.Type.CBRANCH:
                leader_lines.add(i + 1)
                _, _, true_target, false_target = code_instr
                entry_branch_targets[curr_entry].add(true_target)
                entry_branch_targets[curr_entry].add(false_target)
        entry_exit_line[curr_entry] = len(ircode) - 1

        # make instructions subject to deviation leaders
        curr_entry = None
        for i, code_instr in enumerate(ircode):
            instr_type = Instruction.type_of(code_instr)
            if instr_type == Instruction.Type.DEFINE:
                curr_entry = code_instr[1]
            elif instr_type == Instruction.Type.LABEL:
                label = f"%{code_instr[0]}"
                if label in entry_branch_targets[curr_entry]:
                    leader_lines.add(i)
                    entry_leaders_to_lines[curr_entry][label] = i

        # sanity check
        assert leader_lines == set(
            line
            for leader_to_line in entry_leaders_to_lines.values()
            for line in leader_to_line.values()
        )

        for entry, leader_to_line in entry_leaders_to_lines.items():
            blocks = {}
            line_to_leader = sorted((line, leader) for leader, line in leader_to_line.items())

            # create blocks from leaders' starting lines
            exit_line = entry_exit_line[entry]
            for (start, leader), (end, _) in zip(line_to_leader, line_to_leader[1:] + [(exit_line + 1, None)]):
                block = Block(leader)
                block.extend(ircode[start:end])
                if not blocks:
                    self.entries[entry] = block
                blocks[leader] = block

            # connect blocks that belong to the same function
            for (start, leader), (end, next_leader) in zip(line_to_leader, line_to_leader[1:] + [(exit_line + 1, None)]):
                block = blocks[leader]
                last_instr = block.instructions[-1]
                instr_type = Instruction.type_of(last_instr)

                if instr_type == Instruction.Type.JUMP:
                    _, target = last_instr
                    block.sucessors.append(blocks[target])
                    blocks[target].predecessors.append(block)

                elif instr_type == Instruction.Type.CBRANCH:
                    _, _, true_target, false_target = last_instr
                    block.sucessors.append(blocks[true_target])
                    block.sucessors.append(blocks[false_target])
                    blocks[true_target].predecessors.append(block)
                    blocks[false_target].predecessors.append(block)

                elif instr_type != Instruction.Type.RETURN:
                    print(">>>", last_instr, instr_type)
                    print(">>>", start, leader, end, next_leader)
                    block.sucessors.append(blocks[next_leader])
                    blocks[next_leader].predecessors.append(block)

            print(f"\nentry={entry}")
            for block in blocks.values():
                print(" ", block)

        print(f"\nentries={', '.join(self.entries.keys())}")
