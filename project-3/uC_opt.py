from uC_CFG import *
from uC_blocks import *

###########################################################
## uC Code Optimizer ######################################
###########################################################


class Optimizer:
    @staticmethod
    def constant_folding(cfg: ControlFlowGraph):
        for entry in cfg.entries.keys():
            for block in cfg.entry_blocks(entry):
                constant_value = {}
                for i in range(len(block.instructions)):
                    instr = block.instructions[i]
                    instr_type = Instruction.type_of(instr)
                    if instr_type == Instruction.Type.OP:
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
                        var = constant_value.get(var, var)
                        if not isinstance(var, str):
                            constant_value[target] = var
                            block.instructions[i] = (op, var, target)

    @staticmethod
    def constant_propagation(cfg: ControlFlowGraph):
        pass

    @staticmethod
    def dead_code_elimination(cfg: ControlFlowGraph):
        pass
