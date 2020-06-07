from copy import copy

from uC_CFG import *
from uC_blocks import *

###########################################################
## uC Data Flow Analysis (DFA) ############################
###########################################################


def _is_def(instr):
    instr_type = Instruction.type_of(instr)

    if instr_type == Instruction.Type.CALL:
        return len(instr) == 3  # target is optional

    return instr_type in [
        Instruction.Type.LOAD,
        Instruction.Type.STORE,
        Instruction.Type.LITERAL,
        Instruction.Type.ELEM,
        Instruction.Type.OP,
        Instruction.Type.READ,
    ]


class DataFlowAnalysis:
    @staticmethod
    def reaching_definitions(cfg: ControlFlowGraph):
        for entry in cfg.entries.keys():

            # make gen and kill sets for every line in a block
            block_gen, block_kill = {}, {}
            block_defs = {}  # maps variables to definitions (lines) in a block

            for block in cfg.entry_blocks(entry):
                label = block.label
                block_gen[label], block_kill[label] = {}, {}
                block_defs[label] = {}
                for i, instr in enumerate(block.instructions):
                    if _is_def(instr):
                        print("def @", i, "of", label)
                        target = instr[-1]
                        block_gen[label][i] = instr
                        block_kill[label][i] = copy(block_defs[label].get(target, []))
                        block_defs[label].setdefault(target, []).append(i)

            print(f"block_gen:\n   ", "\n   ".join(f"{k}: {v}" for k, v in block_gen.items()))
            print(f"block_kill:\n   ", "\n   ".join(f"{k}: {v}" for k, v in block_kill.items()))
            print(f"block_defs:\n   ", "\n   ".join(f"{k}: {v}" for k, v in block_defs.items()))

            # make in and out sets for every line in a block
            block_in, block_out = {}, {}

