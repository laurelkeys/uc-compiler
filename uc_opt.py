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
        # NOTE in this case we can't use the label to check for visited blocks
        #      as we are walking through every basic block in the CFG (i.e. we
        #      are not restricted to a single function, so labels can be reused)

        def visit(block):
            if block not in visited:
                visited.add(block)
                yield block
                for predecessor in block.predecessors:
                    yield from visit(predecessor)

        for predecessor in self.exit.predecessors:
            yield from visit(predecessor)

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

###########################################################
## uC Data Flow Analysis (DFA) ############################
###########################################################

class DataFlow:
    class LivenessAnalysis:
        @staticmethod
        def compute(cfg: ControlFlowGraph):
            for block in cfg.blocks_from_entry():
                # update gen and kill per line
                block.gen_kill_per_line = DataFlow.LivenessAnalysis.compute_gen_kill(block)
                # update the block's gen and kill
                block.gen_kill = DataFlow.LivenessAnalysis.compute_block_gen_kill(
                    block.gen_kill_per_line
                )

            # update the block's in and out
            DataFlow.LivenessAnalysis.compute_blocks_in_out(cfg)

        @staticmethod
        def compute_blocks_in_out(cfg):
            changed = True
            while changed:
                changed = False
                for block in cfg.blocks_from_exit():
                    before = block.in_out

                    block_out = set(cfg.globals.keys())  # start with all global variables
                    for succ in block.successors:
                        block_out = block_out.union(succ.in_out.in_)

                    block_gen, block_kill = block.gen_kill
                    block_in = block_gen.union(block_out - block_kill)
                    block.in_out = In_Out(block_in, block_out)

                    changed |= before != block.in_out

            # update in and out per line
            for block in cfg.blocks_from_exit():
                block.in_out_per_line = DataFlow.LivenessAnalysis.compute_in_out(
                    block, block.gen_kill_per_line, successors_in=block.in_out.out
                )

        @staticmethod
        def compute_in_out(block, gen_kill_list, successors_in):
            in_out_list = []
            for instr, gen_kill in zip(block.instructions[::-1], gen_kill_list[::-1]):
                out = successors_in
                gen, kill = gen_kill
                in_ = gen.union(out - kill)

                successors_in = in_
                in_out_list.append(In_Out(in_, out))

            return in_out_list[::-1]

        @staticmethod
        def compute_block_gen_kill(gen_kill_list):
            block_gen, block_kill = gen_kill_list[-1]
            for gen, kill in gen_kill_list[-2::-1]:
                block_gen = gen.union(block_gen - kill)
                block_kill = block_kill.union(kill)

            return Gen_Kill(block_gen, block_kill)

        @staticmethod
        def compute_gen_kill(block):
            gen_kill_list = []
            for instr in block.instructions:
                instr_type = Instruction.type_of(instr)
                gen_kill = Gen_Kill(set(), set())

                if instr_type in [
                    Instruction.Type.LOAD,
                    Instruction.Type.FPTOSI,
                    Instruction.Type.SITOFP,
                ]:
                    _, x, t = instr
                    gen_kill = Gen_Kill({x}, {t})

                elif instr_type == Instruction.Type.STORE:
                    op, x, t = instr
                    if "*" in op:
                        gen_kill = Gen_Kill({x, t}, set())
                    else:
                        gen_kill = Gen_Kill({x}, {t})

                elif instr_type == Instruction.Type.LITERAL:
                    _, _, t = instr
                    gen_kill = Gen_Kill(set(), {t})

                elif instr_type == Instruction.Type.ELEM:
                    _, arr, idx, t = instr
                    gen_kill = Gen_Kill({arr, idx}, {t})

                elif instr_type == Instruction.Type.OP:
                    if len(instr) == 3:  # boolean not (!)
                        _, x, t = instr
                        gen_kill = Gen_Kill({x}, {t})
                    else:
                        _, left, right, t = instr
                        gen_kill = Gen_Kill({left, right}, {t})

                elif instr_type == Instruction.Type.CBRANCH:
                    _, expr_test, _, _ = instr
                    gen_kill = Gen_Kill({expr_test}, set())

                elif instr_type == Instruction.Type.CALL and len(instr) == 3:
                    _, _, t = instr
                    gen_kill = Gen_Kill(set(), {t})

                elif instr_type == Instruction.Type.RETURN and len(instr) == 2:
                    _, ret_value = instr
                    gen_kill = Gen_Kill({ret_value}, set())

                elif instr_type == Instruction.Type.PARAM:
                    _, x = instr
                    gen_kill = Gen_Kill({x}, set())

                elif instr_type == Instruction.Type.READ:
                    _, x = instr
                    gen_kill = Gen_Kill(set(), {x})

                elif instr_type == Instruction.Type.PRINT and len(instr) == 2:
                    _, x = instr
                    gen_kill = Gen_Kill({x}, set())

                gen_kill_list.append(gen_kill)

            return gen_kill_list

###########################################################
## uC Code Optimizer ######################################
###########################################################

class Optimizer:
    @staticmethod
    def constant_folding_and_propagation(cfg: ControlFlowGraph):
        # print(">> constant folding + propagation <<")

        # NOTE reaching definitions's values are implicitly calculated below,
        #      unlike dead code elimination, where we call liveness analysis

        for block in cfg.blocks_from_entry():
            constant_value = {}
            for i in range(len(block.instructions)):
                instr = block.instructions[i]
                instr_type = Instruction.type_of(instr)

                if instr_type == Instruction.Type.OP:
                    if len(instr) == 3:  # boolean not (!)
                        op, var, target = instr
                        opcode, *optype = op.split("_")
                        var = constant_value.get(var, var)
                        if not isinstance(var, str):
                            constant_value[target] = int(not var)
                            block.instructions[i] = (f"literal_{'_'.join(optype)}", var, target)
                    else:
                        op, left, right, target = instr
                        opcode, *optype = op.split("_")
                        left = constant_value.get(left, left)
                        right = constant_value.get(right, right)
                        if not isinstance(left, str) and not isinstance(right, str):
                            value = Instruction.fold[opcode](left, right)
                            constant_value[target] = value
                            if optype[0] != "bool":  # NOTE there's no literal_bool
                                block.instructions[i] = (
                                    f"literal_{'_'.join(optype)}",
                                    value,
                                    target,
                                )

                elif Instruction.is_def(instr) and instr_type != Instruction.Type.ELEM:
                    op, var, target = instr
                    opcode, *optype = op.split("_")
                    var = constant_value.get(var, var)
                    if not isinstance(var, str) and len(optype) <= 1:
                        constant_value[target] = var
                        block.instructions[i] = (f"literal_{'_'.join(optype)}", var, target)

                elif instr_type == Instruction.Type.FPTOSI:
                    op, var, target = instr
                    var = constant_value.get(var, var)
                    if not isinstance(var, str):
                        constant_value[target] = int(var)
                        block.instructions[i] = ("literal_int", int(var), target)

                elif instr_type == Instruction.Type.SITOFP:
                    op, var, target = instr
                    var = constant_value.get(var, var)
                    if not isinstance(var, str):
                        constant_value[target] = float(var)
                        block.instructions[i] = ("literal_float", float(var), target)

                elif instr_type == Instruction.Type.CBRANCH:
                    op, expr, true_target, false_target = instr
                    expr = constant_value.get(expr, expr)
                    if not isinstance(expr, str):
                        if bool(expr):
                            block.instructions[i] = ("jump", true_target)
                            for succ in block.successors:
                                if succ.label == false_target:
                                    cfg.remove_block(succ)
                                    break
                            block.successors = [
                                succ for succ in block.successors if succ.label != false_target
                            ]
                        else:
                            block.instructions[i] = ("jump", false_target)
                            for succ in block.successors:
                                if succ.label == true_target:
                                    cfg.remove_block(succ)
                                    break
                            block.successors = [
                                succ for succ in block.successors if succ.label != true_target
                            ]

        # print("\n".join(Instruction.prettify(cfg.build_code())))
        # print(">> constant folding + propagation <<\n")

    @staticmethod
    def dead_code_elimination(cfg: ControlFlowGraph):
        # print(">> dead code elimination <<")

        changed = True
        while changed:
            DataFlow.LivenessAnalysis.compute(cfg)
            # print("\nChanging.....")
            changed = False

            for block in cfg.blocks_from_exit():
                # print("block", block.label)
                new_instructions = []
                for instr, (_, out) in zip(block.instructions[::-1], block.in_out_per_line[::-1]):
                    instr_type = Instruction.type_of(instr)
                    is_dead = False

                    if instr_type in [
                        # Instruction.Type.ALLOC,
                        Instruction.Type.LOAD,
                        Instruction.Type.FPTOSI,
                        Instruction.Type.SITOFP,
                        Instruction.Type.LITERAL,
                        Instruction.Type.ELEM,
                        Instruction.Type.OP,
                    ]:
                        is_dead = instr[-1] not in out
                    elif instr_type == Instruction.Type.STORE:
                        op, _, target = instr
                        opcode, *optype = op.split("_")
                        if "*" not in optype:  # don't remove store on pointers
                            is_dead = target not in out

                    if not is_dead:
                        new_instructions.append(instr)  # keep this instruction
                    # else:
                    #     print("- killed:", instr)

                    changed |= is_dead

                block.instructions = new_instructions[::-1]

        # print("\n".join(Instruction.prettify(cfg.build_code())))
        # print(">> dead code elimination <<\n")

    @staticmethod
    def post_process_blocks(cfg: ControlFlowGraph):
        # print(">> post processing <<")

        # Remove unused allocs
        for entry in cfg.entries:
            # get allocs and used vars
            allocs, used = {}, set()
            for block in cfg.blocks_of_entry(entry):
                for line, instr in enumerate(block.instructions):
                    instr_type = Instruction.type_of(instr)
                    if instr_type == Instruction.Type.ALLOC:
                        allocs[instr[-1]] = (line, block)
                    elif instr_type == Instruction.Type.CBRANCH:
                        _, used_var, _, _ = instr
                        used.add(used_var)
                    elif instr_type not in [
                        Instruction.Type.JUMP,
                        Instruction.Type.LABEL,
                    ]:
                        _, *used_vars = instr
                        used.update(used_vars)

            # kill unused vars
            to_kill = {}
            for var_name, (line, block) in allocs.items():
                if var_name not in used:
                    to_kill.setdefault(block, []).append(line)
            for block, lines_to_kill in to_kill.items():
                block.instructions = [
                    instr
                    for line, instr in enumerate(block.instructions)
                    if line not in lines_to_kill
                ]

        # Check branched blocks for single jump instruction
        for block in cfg.blocks_from_entry():
            if len(block.instructions) == 2:
                first_instr, last_instr = block.instructions
                if (
                    Instruction.type_of(last_instr) == Instruction.Type.JUMP
                    and Instruction.type_of(first_instr) == Instruction.Type.LABEL
                ):
                    assert len(block.successors) == 1
                    block.successors[0].predecessors.remove(block)
                    block.successors[0].predecessors.extend(block.predecessors)

                    _, jump_label = last_instr

                    for pred in block.predecessors:
                        pred.successors.remove(block)
                        pred.successors.append(block.successors[0])

                        last_instr_pred = pred.instructions[-1]
                        instr_type_pred = Instruction.type_of(last_instr_pred)

                        if instr_type_pred == Instruction.Type.JUMP:
                            pred.instructions[-1] = ("jump", jump_label)
                        elif instr_type_pred == Instruction.Type.CBRANCH:
                            op, expr, true_target, false_target = last_instr_pred
                            if true_target == block.label:
                                true_target = jump_label
                            if false_target == block.label:
                                false_target = jump_label
                            pred.instructions[-1] = (op, expr, true_target, false_target)
                        else:
                            assert False

        # Remove global unused vars
        code_functions = []
        for block in cfg.blocks_from_entry():
            code_functions.extend(block.instructions)

        code_functions_str = "\n".join(Instruction.prettify(code_functions))

        unused = []
        for var_name in cfg.globals:
            if code_functions_str.find(var_name) < 0:
                unused.append(var_name)
        for var in unused:
            cfg.globals.pop(var)

        # print("\n".join(Instruction.prettify(cfg.build_code())))
        # print(">> post processing <<\n")

    @staticmethod
    def post_process_code(code):
        # remove jumps to block right below
        to_remove = []
        for i, line in enumerate(code[:-1]):
            if line[0] == 'jump':
                next_instr = code[i + 1]
                if (
                    len(next_instr) == 1
                    and next_instr[0] not in ['return_void', 'print_void']
                    and line[1][1:] == next_instr[0]
                ):
                    to_remove.append(i)
        code = [line for i, line in enumerate(code) if i not in to_remove]
        return code
