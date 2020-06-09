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
                is_constant = {}
                for i in range(len(block.instructions)):
                    instr = block.instructions[i]
                    instr_type = Instruction.type_of(instr)
                    if Instruction.is_def(instr):
                        if instr_type == Instruction.Type.OP:
                            _, left, right, target = instr
                            print("target", target, "|", left, right, "| instr", instr)
                        elif instr_type == Instruction.Type.ELEM:
                            _, arr, idx, target = instr
                            print("target", target, "|", arr, idx, "| instr", instr)
                        else:
                            _, var, target = instr
                            print("target", target, "|", var, "| instr", instr)


    @staticmethod
    def constant_propagation(cfg: ControlFlowGraph):
        pass

    @staticmethod
    def dead_code_elimination(cfg: ControlFlowGraph):
        pass
