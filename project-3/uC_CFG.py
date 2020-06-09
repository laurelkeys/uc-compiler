import os

from collections import namedtuple
from enum import Enum, unique

from graphviz import Digraph

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
                entry_leaders_to_lines[curr_entry] = {f"%entry": i}

            elif instr_type == Instruction.Type.JUMP:
                # if Instruction.type_of(ircode[i + 1]) != Instruction.Type.JUMP:
                leader_lines.add(i + 1)  # HACK (e.g. if-body ending with return)
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

        leader_lines = list(sorted(leader_lines))
        exit_line = { leader_lines[-1]: len(ircode) - 1 }
        for start, end in zip(leader_lines[:-1], leader_lines[1:]):
            exit_line[start] = end - 1

        for entry, leader_to_line in entry_leaders_to_lines.items():
            blocks = {}
            line_to_leader = sorted((line, leader) for leader, line in leader_to_line.items())

            # create blocks from leaders' starting lines
            for start, leader in line_to_leader:
                block = Block(leader)
                block.extend(ircode[start : exit_line[start] + 1])
                if not blocks:
                    self.entries[entry] = block
                blocks[leader] = block

            # connect blocks that belong to the same function
            for (start, leader), (_, next_leader) in zip(line_to_leader[:-1], line_to_leader[1:]):
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
                    block.sucessors.append(blocks[next_leader])
                    blocks[next_leader].predecessors.append(block)

            # remove immediate dead blocks
            for block in blocks.values():
                if not block.predecessors and block.label != f"%entry":
                    for suc in block.sucessors:
                        suc.predecessors.remove(block)

    def simplify(self):
        ''' Attempts to merge basic blocks.\n
            See https://en.wikipedia.org/wiki/Dominator_(graph_theory)#Algorithms
        '''
        for entry in self.entries.keys():
            blocks_to_merge = []

            # NOTE special case algorithm
            for block in self.entry_blocks(entry):
                if len(block.sucessors) == 1:
                    sucessor = block.sucessors[0]
                    if len(sucessor.predecessors) == 1:
                        blocks_to_merge.append((block, sucessor))

            for top, bottom in blocks_to_merge:
                # fix code
                if Instruction.type_of(top.instructions[-1]) == Instruction.Type.JUMP:
                    top.instructions = top.instructions[:-1] + bottom.instructions[1:]
                else:
                    top.instructions = top.instructions + bottom.instructions[1:]
                # fix edges
                top.sucessors = bottom.sucessors
                for suc in bottom.sucessors:
                    suc.predecessors.remove(bottom)
                    suc.predecessors.append(top)

    def entry_blocks(self, entry_name):
        ''' Returns a generator for the blocks of the entry. '''
        visited = set()

        def visit(block):
            if block.label not in visited:
                visited.add(block.label)
                yield block
                for sucessor in block.sucessors:
                    yield from visit(sucessor)

        yield from visit(self.entries[entry_name])


class GraphViewer:
    @staticmethod
    def view_entry(entry_name, entry_block):
        fname = f"graphviz/{entry_name}.gv"
        try:
            os.remove(fname)
        except OSError:
            pass
        g = Digraph("g", filename=fname, node_attr={"shape": "record"})

        def format_line(instr):
            line = " ".join(map(str, instr))
            return f"{line}:" if len(instr) == 1 and instr[0].isdigit() else f"  {line}"

        def _visit(block):
            name = block.label
            label = "{" + name + ":\l\t"
            for instr in block.instructions[1:]:
                label += format_line(instr) + "\l\t"
            label += "}"
            g.node(name, label)

            for pred in block.predecessors:
                g.edge(pred.label, name)

            if name == "entry":
                g.node(entry_name, label=None, _attributes={"shape": "ellipse"})
                g.edge(entry_name, name)

        visited = set()

        def visit(block):
            if block not in visited:
                visited.add(block)
                _visit(block)
                for suc in block.sucessors:
                    visit(suc)

        visit(entry_block)

        g.view()

