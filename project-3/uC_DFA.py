from collections import namedtuple
from copy import copy

from uC_CFG import *
from uC_blocks import *

###########################################################
## uC Data Flow Analysis (DFA) ############################
###########################################################


In_Out = namedtuple(typename="In_Out", field_names=["in_", "out"])
Gen_Kill = namedtuple(typename="Gen_Kill", field_names=["gen", "kill"])


class DataFlow:
    # @staticmethod
    # def compute_defs(cfg: ControlFlowGraph, entry_name):
    #     pass

    class ReachingDefinitions:
        @staticmethod
        def compute_gen_kill(block):
            for instr in block.instructions:
                raise NotImplementedError

        @staticmethod
        def compute(cfg: ControlFlowGraph):
            for entry in cfg.entries.keys():
                raise NotImplementedError

    class LivenessAnalysis:
        @staticmethod
        def compute(cfg: ControlFlowGraph):
            for entry in cfg.entries:
                print("\n\nentry", entry)
                for block in cfg.entry_blocks(entry):
                    print("\nblock", block.label)
                    gen_kill_list = DataFlow.LivenessAnalysis.compute_gen_kill(block)
                    in_out_list = DataFlow.LivenessAnalysis.compute_in_out(block, gen_kill_list)
                    for gen_kill, in_out, instr in zip(gen_kill_list, in_out_list, block.instructions):
                        print(str(instr).ljust(40), in_out)
                        print(str(instr).ljust(40), gen_kill)

        @staticmethod
        def compute_in_out(block, gen_kill_list):
            in_out_list = []
            successors_in = set()  # NOTE the successor of the last line is empty
            for instr, gen_kill in zip(block.instructions[::-1], gen_kill_list[::-1]):
                out = successors_in
                gen, kill = gen_kill
                in_ = gen.union(out - kill)

                successors_in = in_
                in_out_list.append(In_Out(in_, out))

            return in_out_list[::-1]


        @staticmethod
        def compute_gen_kill(block):
            gen_kill_list = []
            for instr in block.instructions:
                instr_type = Instruction.type_of(instr)

                gen_kill = Gen_Kill(set(), set())
                if instr_type in [
                    Instruction.Type.LOAD,
                    Instruction.Type.STORE,
                    Instruction.Type.FPTOSI,
                    Instruction.Type.SITOFP,
                ]:
                    _, x, t = instr
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