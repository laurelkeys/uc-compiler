import os

from collections import namedtuple
from enum import Enum, unique

from graphviz import Digraph

from uc_blocks import *
from uc_ir import Instruction

###########################################################
## uC Control-Flow Graph (CFG) ############################
###########################################################


class ControlFlowGraph:
    ''' Control-flow graph (CFG) representation of a uC program. '''

    def __init__(self, ircode):
        ''' Represent the IR code as a graph of basic blocks. '''
        self.entries = {}
        self.exit = Block(r"%exit")  # dummy block used for backward analysis
        self.globals = {}  # store global variable declarations

        leader_lines = set()
        entry_exit_line = {}
        entry_branch_targets = {}
        entry_leaders_to_lines = {}

        # make defines and instructions following deviations leaders
        curr_entry = None
        for i, code_instr in enumerate(ircode):
            instr_type = Instruction.type_of(code_instr)

            if instr_type == Instruction.Type.GLOBAL:
                _, varname, *_ = code_instr
                self.globals[varname] = code_instr

            elif instr_type == Instruction.Type.DEFINE:
                leader_lines.add(i)
                if curr_entry is not None:
                    entry_exit_line[curr_entry] = i - 1
                curr_entry = code_instr[1]
                entry_branch_targets[curr_entry] = set()
                entry_leaders_to_lines[curr_entry] = {r"%entry": i}

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

        leader_lines = list(sorted(leader_lines))
        exit_line = {leader_lines[-1]: len(ircode) - 1}
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
                    block.successors.append(blocks[target])
                    blocks[target].predecessors.append(block)

                elif instr_type == Instruction.Type.CBRANCH:
                    _, _, true_target, false_target = last_instr
                    block.successors.append(blocks[true_target])
                    block.successors.append(blocks[false_target])
                    blocks[true_target].predecessors.append(block)
                    blocks[false_target].predecessors.append(block)

                elif instr_type != Instruction.Type.RETURN:
                    block.successors.append(blocks[next_leader])
                    blocks[next_leader].predecessors.append(block)

            # remove immediate dead blocks
            for block in blocks.values():
                if not block.predecessors and block.label != r"%entry":
                    for succ in block.successors:
                        succ.predecessors.remove(block)
                if not block.successors:
                    self.exit.predecessors.append(block)

    def simplify(self):
        ''' Attempts to merge basic blocks.\n
            See https://en.wikipedia.org/wiki/Dominator_(graph_theory)#Algorithms
        '''
        for entry in self.entries:
            blocks_to_merge = []

            # NOTE given the restrictions of basic blocks, such as linearity,
            #      we can use a simpler dominance algorithm to find mergings:
            for block in self.blocks_of_entry(entry):
                if len(block.successors) == 1:
                    successor = block.successors[0]
                    if len(successor.predecessors) == 1:
                        blocks_to_merge.append((block, successor))

            for top, bottom in blocks_to_merge:
                # fix code
                if Instruction.type_of(top.instructions[-1]) == Instruction.Type.JUMP:
                    top.instructions = top.instructions[:-1] + bottom.instructions[1:]
                else:
                    top.instructions = top.instructions + bottom.instructions[1:]
                # fix edges
                top.successors = bottom.successors
                for succ in bottom.successors:
                    succ.predecessors.remove(bottom)
                    succ.predecessors.append(top)
                # fix exit
                if bottom in self.exit.predecessors:
                    self.exit.predecessors.remove(bottom)
                    self.exit.predecessors.append(top)

    def blocks_of_entry(self, entry):
        ''' Returns a forward generator for the blocks from a given entry. '''
        visited = set()

        def visit(block):
            if block.label not in visited:
                visited.add(block.label)
                yield block
                for successor in block.successors:
                    yield from visit(successor)

        yield from visit(self.entries[entry])

    def blocks_from_entry(self):
        ''' Returns a forward generator for all blocks. '''
        for entry in self.entries:
            yield from self.blocks_of_entry(entry)

    def blocks_from_exit(self):
        ''' Returns a backward generator for all blocks. '''
        visited = set()

        def visit(block):
            if block.label not in visited:
                visited.add(block.label)
                yield block
                for predecessor in block.predecessors:
                    yield from visit(predecessor)

        yield from visit(self.exit)

    def build_code(self):
        ''' Rebuild the program code from the instructions of each block. '''
        code = []
        code.extend(self.globals.values())
        for block in self.blocks_from_entry():
            code.extend(block.instructions)
        return code

    def remove_block(self, block):
        ''' Remove edges linking the given block to others on the CFG. '''
        for succ in block.successors:
            succ.predecessors.remove(block)
        for pred in block.predecessors:
            pred.successors.remove(block)


class GraphViewer:
    @staticmethod
    def view_entry(entry_name, entry_block, save_folder="graphviz", save_as_png=True):
        g = Digraph(
            name=entry_name,
            directory=save_folder,
            node_attr={"shape": "record"},
            format="png" if save_as_png else "pdf",
        )

        visited = set()

        def visit(block):
            name = block.label
            if name not in visited:
                node_label = "{" + name + ":\l\t"
                for instr in block.instructions[1:]:
                    node_label += " ".join(map(str, instr)) + "\l\t"
                node_label += "}"
                g.node(name, node_label)
                for pred in block.predecessors:
                    if len(pred.successors) == 2:
                        g.edge(pred.label, name, " T" if block == pred.successors[0] else " F")
                    else:
                        g.edge(pred.label, name)
                if name == r"%entry":
                    g.node(entry_name, label=None, _attributes={"shape": "ellipse"})
                    g.edge(entry_name, name)

                visited.add(name)
                for successor in block.successors:
                    visit(successor)

        visit(entry_block)

        g.view()
