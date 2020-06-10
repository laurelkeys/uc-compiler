from uC_CFG import *
from uC_blocks import *

###########################################################
## uC Code Optimizer ######################################
###########################################################


class Optimizer:
    @staticmethod
    def constant_folding_and_propagation(cfg: ControlFlowGraph):
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
        print(">> dead code elimination <<")
        for block in cfg.exit_blocks():
            print(block.label)
        print(">> dead code elimination <<")
