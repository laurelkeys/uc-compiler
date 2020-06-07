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
                    print(curr_entry, "ends at", i-1)
                curr_entry = code_instr[1]
                entry_branch_targets[curr_entry] = set()
                entry_leaders_to_lines[curr_entry] = { "entry": i }

            elif instr_type == Instruction.Type.JUMP:
                leader_lines.add(i + 1)
                _, target = code_instr
                entry_branch_targets[curr_entry].add(target)

            elif instr_type == Instruction.Type.CBRANCH:
                leader_lines.add(i + 1)
                _, _, true_target, false_target = code_instr
                entry_branch_targets[curr_entry].add(true_target)
                entry_branch_targets[curr_entry].add(false_target)

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
            print(entry)
            for line, leader in sorted((line, leader) for leader, line in leader_to_line.items()):
                print(" ", leader, ":", line)

        leader_lines = list(sorted(leader_lines))

        # # create blocks from leaders' starting lines
        entry_lines_to_leaders = {
            entry: {line: leader for leader, line in leader_to_line.items()}
            for entry, leader_to_line in entry_leaders_to_lines.items()
        }
        print("\n", leader_lines)
        print("\n", entry_leaders_to_lines)
        print("\n", entry_lines_to_leaders)
        exit()

        leaders = {}
        for start, end in zip(leader_lines, leader_lines[1:] + [len(ircode)]):
            label = line_to_leader[start]
            if label[0] == "@":
                leaders[label] = Block("entry")
                leaders[label].extend(ircode[start+1:end])
                self.entries[label] = leaders[label]
            else:
                leaders[label] = Block(label)
                leaders[label].extend(ircode[start:end])

        # # connect blocks that belong to the same function
        # for (label, block), next_leader_line in zip(leaders.items(), leader_lines[1:]):
        #     last_instr = block.instructions[-1]
        #     instr_type = Instruction.type_of(last_instr)

        #     if instr_type == Instruction.Type.JUMP:
        #         _, target = last_instr
        #         block.sucessors.append(leaders[target])
        #         leaders[target].predecessors.append(block)

        #     elif instr_type == Instruction.Type.CBRANCH:
        #         _, _, true_target, false_target = last_instr
        #         block.sucessors.append(leaders[true_target])
        #         block.sucessors.append(leaders[false_target])
        #         leaders[true_target].predecessors.append(block)
        #         leaders[false_target].predecessors.append(block)

        #     elif instr_type != Instruction.Type.RETURN:
        #         next_leader_label = line_to_leader[next_leader_line]
        #         block.sucessors.append(leaders[next_leader_label])
        #         leaders[next_leader_label].predecessors.append(block)

        # print("\n" + "\n".join(map(str, leaders.values())))

        # print(leader_to_line)
        # print(line_to_leader)
        # print(self.entries)
