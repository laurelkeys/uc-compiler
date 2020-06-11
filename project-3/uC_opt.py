from uC_DFA import DataFlow
from uC_CFG import *
from uC_blocks import *

###########################################################
## uC Code Optimizer ######################################
###########################################################


class Optimizer:
    @staticmethod
    def constant_folding_and_propagation(cfg: ControlFlowGraph):
        DataFlow.ReachingDefinitions.compute(cfg)
        print(">> constant folding + propagation <<")
        for entry in cfg.entries.keys():
            for block in cfg.entry_blocks(entry):
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
                            continue

                        op, left, right, target = instr
                        opcode, *optype = op.split("_")
                        left = constant_value.get(left, left)
                        right = constant_value.get(right, right)
                        if not isinstance(left, str) and not isinstance(right, str):
                            value = Instruction.fold[opcode](left, right)
                            constant_value[target] = value
                            block.instructions[i] = (f"literal_{'_'.join(optype)}", value, target)

                    elif Instruction.is_def(instr) and instr_type != Instruction.Type.ELEM:
                        op, var, target = instr
                        opcode, *optype = op.split("_")
                        var = constant_value.get(var, var)
                        if not isinstance(var, str):
                            constant_value[target] = var
                            block.instructions[i] = (f"literal_{'_'.join(optype)}", var, target)

                    elif instr_type == Instruction.Type.FPTOSI:
                        _, var, target = instr
                        var = constant_value.get(var, var)
                        if not isinstance(var, str):
                            constant_value[target] = int(var)
                            block.instructions[i] = (f"literal_int", int(var), target)

                    elif instr_type == Instruction.Type.SITOFP:
                        _, var, target = instr
                        var = constant_value.get(var, var)
                        if not isinstance(var, str):
                            constant_value[target] = float(var)
                            block.instructions[i] = (f"literal_float", float(var), target)

                    # else: ALLOC, GLOBAL, ELEM, LABEL, JUMP, CBRANCH, DEFINE, RETURN, PARAM, READ

                print("\n".join(Instruction.prettify(block.instructions)))
        print(">> constant folding + propagation <<")

    @staticmethod
    def dead_code_elimination(cfg: ControlFlowGraph):
        DataFlow.LivenessAnalysis.compute(cfg)
        print(">> dead code elimination <<")
        for block in cfg.exit_blocks():
            # block_gen, block_kill = block.gen_kill
            # block_in, block_out = block.in_out
            print(block.label)
            new_instructions = []
            for instr, (_, out) in zip(block.instructions[::-1], block.in_out_per_line[::-1]):
                instr_type = Instruction.type_of(instr)

                is_dead = False
                if instr_type in [
                    Instruction.Type.LOAD,
                    Instruction.Type.STORE,
                    Instruction.Type.FPTOSI,
                    Instruction.Type.SITOFP,
                    Instruction.Type.LITERAL,
                    Instruction.Type.ELEM,
                    Instruction.Type.OP,
                    Instruction.Type.CBRANCH,
                    Instruction.Type.PARAM,
                    Instruction.Type.READ,
                ]:
                    is_dead = instr[-1] not in out

                elif instr_type == Instruction.Type.CALL and len(instr) == 3:
                    is_dead = instr[-1] not in out

                elif instr_type == Instruction.Type.RETURN and len(instr) == 2:
                    is_dead = instr[-1] not in out

                elif instr_type == Instruction.Type.PRINT and len(instr) == 2:
                    is_dead = instr[-1] not in out

                if not is_dead:
                    new_instructions.append(instr)
                else:
                    print("KILLING THIS BEAAACH", instr)

            block.instructions = new_instructions[::-1]

        print(">> dead code elimination <<")
