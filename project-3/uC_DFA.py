from copy import copy

from uC_CFG import *
from uC_blocks import *

###########################################################
## uC Data Flow Analysis (DFA) ############################
###########################################################


class DataFlowAnalysis:
    @staticmethod
    def gen_kill_defs(cfg: ControlFlowGraph, entry_name):
        ''' Returns the GEN, KILL and DEFS sets for every block of an entry. '''
        block_gen, block_kill = {}, {}  # sets for every line in a block
        block_defs = {}  # maps variables to definition lines in a block

        for block in cfg.entry_blocks(entry_name):
            label = block.label
            block_gen[label], block_kill[label] = {}, {}
            block_defs[label] = {}
            for i, instr in enumerate(block.instructions):
                if Instruction.is_def(instr):
                    target = instr[-1]
                    block_gen[label][i] = instr
                    block_kill[label][i] = copy(block_defs[label].get(target, []))
                    block_defs[label].setdefault(target, []).append(i)

        return block_gen, block_kill, block_defs

    @staticmethod
    def reaching_definitions(cfg: ControlFlowGraph):
        for entry in cfg.entries.keys():
            block_gen, block_kill, block_defs = DataFlowAnalysis.gen_kill_defs(cfg, entry)

            print(f"block_gen:\n   ", "\n   ".join(f"{k}: {v}" for k, v in block_gen.items()))
            print(f"block_kill:\n   ", "\n   ".join(f"{k}: {v}" for k, v in block_kill.items()))
            print(f"block_defs:\n   ", "\n   ".join(f"{k}: {v}" for k, v in block_defs.items()))

            # make in and out sets for every line in a block
            # block_in, block_out = {}, {}

            # last_block_out = None
            # for block in cfg.entry_blocks(entry_name):
            #     label = block.label
            #     block_in[label], block_out[label] = {}, {}
            #     for i, instr in enumerate(block.instructions):
            #         block_in[label][i] = []
            #         # for pred in
