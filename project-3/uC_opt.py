from uC_DFA import DataFlow
from uC_CFG import *
from uC_blocks import *

###########################################################
## uC Code Optimizer ######################################
###########################################################


class Optimizer:
    @staticmethod
    def constant_folding_and_propagation(cfg: ControlFlowGraph):
        # DataFlow.ReachingDefinitions.compute(cfg)
        print(">> constant folding + propagation <<")
        for entry in cfg.entries.keys():
            for block in cfg.entry_blocks(entry):
                constant_value = {}
                for i in range(len(block.instructions)):
                    instr = block.instructions[i]
                    instr_type = Instruction.type_of(instr)

                    if instr_type == Instruction.Type.OP:
                        if len(instr) == 3:  # boolean not (!)
                            op, var_, target = instr
                            opcode, *optype = op.split("_")
                            var = constant_value.get(var_, var_)
                            if not isinstance(var, str):
                                constant_value[target] = int(not var)

                                if not op.startswith("literal_"): print("from:", (op, var_, target))
                                block.instructions[i] = (f"literal_{'_'.join(optype)}", var, target)
                                if not op.startswith("literal_"): print("to  :", block.instructions[i])
                            continue

                        op, left_, right_, target = instr
                        opcode, *optype = op.split("_")
                        left = constant_value.get(left_, left_)
                        right = constant_value.get(right_, right_)
                        if (not isinstance(left, str) and not isinstance(right, str)) :
                                                    #  and optype[0] != "bool"):  # NOTE there's no literal_bool
                            value = Instruction.fold[opcode](left, right)
                            constant_value[target] = value
                            if not op.startswith("literal_"): 
                                print("from:", (op, left_, right_, target))
                                print("r", right, "l", left, 'v', value)
                            if optype[0] != "bool":
                                block.instructions[i] = (f"literal_{'_'.join(optype)}", value, target)
                            if not op.startswith("literal_"): print("to  :", block.instructions[i])

                    elif Instruction.is_def(instr) and instr_type != Instruction.Type.ELEM:
                        op, var_, target = instr
                        opcode, *optype = op.split("_")
                        var = constant_value.get(var_, var_)
                        print(optype)
                        if not isinstance(var, str) and len(optype) <= 1:
                            constant_value[target] = var
                            if not op.startswith("literal_"): print("from:", (op, var_, target))
                            block.instructions[i] = (f"literal_{'_'.join(optype)}", var, target)
                            if not op.startswith("literal_"): print("to  :", block.instructions[i])

                    elif instr_type == Instruction.Type.FPTOSI:
                        op, var, target = instr
                        var = constant_value.get(var, var)
                        if not isinstance(var, str):
                            constant_value[target] = int(var)
                            if not op.startswith("literal_"): print("from:", (op, var, target))
                            block.instructions[i] = (f"literal_int", int(var), target)
                            if not op.startswith("literal_"): print("to  :", block.instructions[i])

                    elif instr_type == Instruction.Type.SITOFP:
                        op, var, target = instr
                        var = constant_value.get(var, var)
                        if not isinstance(var, str):
                            constant_value[target] = float(var)
                            if not op.startswith("literal_"): print("from:", (op, var, target))
                            block.instructions[i] = (f"literal_float", float(var), target)
                            if not op.startswith("literal_"): print("to  :", block.instructions[i])

                    elif instr_type == Instruction.Type.CBRANCH:
                        op, expr_, target_true, target_false = instr
                        expr = constant_value.get(expr_, expr_)
                        if not isinstance(expr, str):
                            if not op.startswith("literal_"): print("from:", (op, expr_, target_true, target_false))
                            if bool(expr):
                                block.instructions[i] = ("jump", target_true)
                                for succ in block.sucessors:
                                    if succ.label == target_false:
                                        cfg.remove_block(succ)
                                        break
                                block.sucessors = [suc for suc in block.sucessors if suc.label != target_false]
                            else:
                                block.instructions[i] = ("jump", target_false)
                                for succ in block.sucessors:
                                    if succ.label == target_true:
                                        cfg.remove_block(succ)
                                        break
                                block.sucessors = [suc for suc in block.sucessors if suc.label != target_true]
                            if not op.startswith("literal_"): print("to  :", block.instructions[i])

                    # else: ALLOC, GLOBAL, ELEM, LABEL, JUMP, CBRANCH, DEFINE, RETURN, PARAM, READ

                print("\n".join(Instruction.prettify(block.instructions)))
        print(">> constant folding + propagation <<")

    @staticmethod
    def dead_code_elimination(cfg: ControlFlowGraph):
        print(">> dead code elimination <<")
        changed = True
        while changed:
            DataFlow.LivenessAnalysis.compute(cfg)
            changed = False
            print("\nCHANGING.....")
            for block in cfg.exit_blocks():
                print(block.label)
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
                        op, var_, target = instr
                        opcode, *optype = op.split("_")
                        if '*' not in optype: # don't remove store on pointers
                            is_dead = instr[-1] not in out

                    if not is_dead:
                        new_instructions.append(instr)
                    else:
                        print("KILLING THIS BEAAACH", instr)

                    changed |= is_dead
                block.instructions = new_instructions[::-1]

        print(">> dead code elimination <<")

    @staticmethod
    def post_process_blocks(cfg: ControlFlowGraph):
        # Remove unused allocs
        for entry in cfg.entries:
            # Get allocs and used vars
            allocs = {}
            used = set()
            for block in cfg.entry_blocks(entry):
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
            for block, lines in to_kill.items():
                block.instructions = [instr for line, instr in enumerate(block.instructions) 
                                        if line not in lines]


        # Check branched blocks for single jump instruction
        for entry in cfg.entries:
            for block in cfg.entry_blocks(entry):
                
                if len(block.instructions) == 2:
                    last_instr = block.instructions[-1]
                    instr_type = Instruction.type_of(last_instr)
                    if instr_type == Instruction.Type.JUMP:
                        assert len(block.sucessors) == 1
                        block.sucessors[0].predecessors.remove(block)
                        block.sucessors[0].predecessors.extend(block.predecessors)

                        _, jump_label = last_instr
                        # jump_label = "%" + jump_label
                        for pred in block.predecessors:
                            pred.sucessors.remove(block)
                            pred.sucessors.append(block.sucessors[0])
                            last_instr_pred = pred.instructions[-1]
                            instr_type_pred = Instruction.type_of(last_instr_pred)

                            if instr_type_pred == Instruction.Type.JUMP:
                                pred.instructions[-1] = ("jump", jump_label)
                            elif instr_type_pred == Instruction.Type.CBRANCH:
                                op, v, l, r = last_instr_pred
                                if l == block.label: l = jump_label
                                if r == block.label: r = jump_label
                                pred.instructions[-1] = (op, v, l, r)
                            else:
                                assert False

        # Remove constant condition ifs