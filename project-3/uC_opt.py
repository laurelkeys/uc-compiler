from uC_DFA import DataFlow
from uC_CFG import *
from uC_blocks import *

###########################################################
## uC Code Optimizer ######################################
###########################################################


class Optimizer:
    @staticmethod
    def constant_folding_and_propagation(cfg: ControlFlowGraph):
        # print(">> constant folding + propagation <<")

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
                next_instr = code[i+1]
                if (len(next_instr) == 1 and
                    next_instr[0] not in ['return_void', 'print_void'] and
                    line[1][1:] == next_instr[0]
                ):
                    to_remove.append(i)
        code = [line for i, line in enumerate(code) if i not in to_remove]
        return code