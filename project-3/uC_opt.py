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
                        if not isinstance(left, str) and not isinstance(right, str) \
                                                     and optype[0] != "bool":  # NOTE there's no literal_bool
                            value = Instruction.fold[opcode](left, right)
                            constant_value[target] = value
                            if not op.startswith("literal_"): print("from:", (op, left_, right_, target))
                            block.instructions[i] = (f"literal_{'_'.join(optype)}", var, target)
                            if not op.startswith("literal_"): print("to  :", block.instructions[i])

                    elif Instruction.is_def(instr) and instr_type != Instruction.Type.ELEM:
                        op, var_, target = instr
                        opcode, *optype = op.split("_")
                        var = constant_value.get(var_, var_)
                        if not isinstance(var, str):
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
                        Instruction.Type.STORE,
                        Instruction.Type.FPTOSI,
                        Instruction.Type.SITOFP,
                        Instruction.Type.LITERAL,
                        Instruction.Type.ELEM,
                        Instruction.Type.OP,
                    ]:
                        is_dead = instr[-1] not in out

                    if not is_dead:
                        new_instructions.append(instr)
                    else:
                        print("KILLING THIS BEAAACH", instr)

                    changed |= is_dead
                block.instructions = new_instructions[::-1]

        print(">> dead code elimination <<")
