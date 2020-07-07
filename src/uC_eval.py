from ctypes import CFUNCTYPE, c_double

import llvmlite.binding as llvm

from uC_LLVMIR import LLVMCodeGenerator, UCLLVM
from uC_parser import UCParser


class CodeEvaluator:
    def __init__(self) -> None:
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        self.target = llvm.Target.from_default_triple()
        self.reset()

    def reset(self):
        self.parser = UCParser()
        self.generator = LLVMCodeGenerator()
        # TODO add built-ins

    def eval(self, uC_code: str, optimize: bool = True):
        ast = self.parser.parse(uC_code)
        llvm_code = self.generator.generate_code(ast)

        llvm_module = llvm.parse_assembly(llvmir=str(llvm_code))
        llvm_module.verify()  # NOTE dump .ll unoptimized code here

        if optimize:
            pmb = llvm.create_pass_manager_builder()
            pm = llvm.create_module_pass_manager()

            # ref.: https://clang.llvm.org/docs/CommandGuide/clang.html#code-generation-options
            pmb.opt_level  = 2  # 0 = -O0,  1 = -O1, 2 = -O2, 3 = -O3
            pmb.size_level = 0  # 0 = none, 1 = -Os, 2 = -Oz

            # ref.: http://llvm.org/docs/Passes.html https://stackoverflow.com/a/15548189
            # pm.add_constant_merge_pass()          # -constmerge
            # pm.add_dead_arg_elimination_pass()    # -deadargelim
            # pm.add_function_attrs_pass()          # -functionattrs
            # pm.add_global_dce_pass()              # -globaldce
            # pm.add_global_optimizer_pass()        # -globalopt
            # pm.add_ipsccp_pass()                  # -ipsccp
            # pm.add_dead_code_elimination_pass()   # -dce
            # pm.add_cfg_simplification_pass()      # -simplifycfg
            # pm.add_gvn_pass()                     # -gvn
            # pm.add_instruction_combining_pass()   # -instcombine
            # pm.add_licm_pass()                    # -licm
            # pm.add_sccp_pass()                    # -sccp
            # pm.add_sroa_pass()                    # -sroa

            pmb.populate(pm)
            pm.run(llvm_module)

            llvm_module.verify()  # NOTE dump .ll optimized code here

        target_machine = self.target.create_target_machine()
        with llvm.create_mcjit_compiler(llvm_module, target_machine) as execution_engine:
            execution_engine.finalize_object()  # NOTE dump .asm machine code here

            fn = llvm_module.get_function(name="main")
            fn_return_type = UCLLVM.Type.Void  # FIXME get the return type of main

            fn_ptr = CFUNCTYPE(fn_return_type)(execution_engine.get_pointer_to_function(fn))
            
            return fn_ptr()  # FIXME args (?)
