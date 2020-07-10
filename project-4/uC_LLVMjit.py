from ctypes import CFUNCTYPE, c_int

import llvmlite.binding as llvm

from uC_LLVMIR import LLVMCodeGenerator, UCLLVM
from uC_parser import UCParser


class LLVMCompiler:
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

    def eval(self, llvm_code, optimize=True, opt_file=None, opt_debug=False):
        llvm_module = llvm.parse_assembly(llvmir=str(llvm_code))
        llvm_module.verify()

        if optimize:
            pmb = llvm.create_pass_manager_builder()
            pm = llvm.create_module_pass_manager()

            # ref.: https://clang.llvm.org/docs/CommandGuide/clang.html#code-generation-options
            pmb.opt_level  = 0  # 0 = -O0,  1 = -O1, 2 = -O2, 3 = -O3
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

            llvm_module.verify()
            if opt_file is not None:
                opt_file.write(str(llvm_module))
            if opt_debug:
                print("----")
                print(str(llvm_module))

        target_machine = self.target.create_target_machine()
        with llvm.create_mcjit_compiler(llvm_module, target_machine) as execution_engine:
            execution_engine.finalize_object()  # NOTE dump .asm machine code here
            execution_engine.run_static_constructors()

            # FIXME get the return type of main
            main = CFUNCTYPE(c_int)(execution_engine.get_function_address(name="main"))

            return main()  # FIXME args (?)
