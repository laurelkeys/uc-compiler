
###########################################################
## uC Interpreter #########################################
###########################################################

# NOTE Given a sequence of instruction tuples such as:
#          code = [ 
#              ('literal_int', 1, '%1'),
#              ('literal_int', 2, '%2'),
#              ('add_int', '%1', '%2, '%3')
#              ('print_int', '%3')
#              ...
#          ]
#
#      The class executes methods self.run_opcode(args), for example:
#          self.run_literal_int(1, '%1')
#          self.run_literal_int(2, '%2')
#          self.run_add_int('%1', '%2', '%3')
#          self.run_print_int('%3')
#          ...

# NOTE To store the values of variables created in the IR, we simply use a dictionary.

# NOTE For built-in function declarations, we allow specific Python modules 
#      (e.g.: print, input, etc.) to be registered with the interpreter.

class Interpreter:
    ''' Runs an interpreter on the generated SSA intermediate code. '''
    
    def __init__(self, name="module"):
        # Dictionary of currently defined variables
        self.vars = {}

    def run(self, ircode):
        ''' Run intermediate code in the interpreter, where `ircode` is a list of instruction tuples.\n            
            Each instruction `(opcode, *args)` is dispatched to a method `self.run_opcode(*args)`.
        '''
        self.pc = 0
        while True:
            try:
                op = ircode[self.pc]
            except IndexError:
                if self.pc > len(ircode):
                    print("Wrong PC %d - terminating" % self.pc)
                return
            self.pc += 1
            opcode = op[0]
            if hasattr(self, f"run_{opcode}"):
                getattr(self, f"run_{opcode}")(*op[1:])
            else:
                print(f"Warning: No run_{opcode}() method")
        
    # TODO Implement methods for different opcodes.
    #      A few sample opcodes are shown below to get you started.

    def run_jump(self, label):
        self.pc = label

    def run_cbranch(self, cond, if_label, else_label):
        if self.vars[cond]:
            self.pc = if_label
        else:
            self.pc = else_label

    def run_literal_int(self, value, target):
        ''' Create a literal integer value. '''
        self.vars[target] = value

    run_literal_float = run_literal_int
    run_literal_char = run_literal_int
    
    def run_add_int(self, left, right, target):
        ''' Add two integer variables. '''
        self.vars[target] = self.vars[left] + self.vars[right]

    run_add_float = run_add_int
    run_add_string = run_add_int

    def run_print_int(self, source):
        ''' Output an integer value. '''
        print(self.vars[source])

    def run_alloc_int(self, name):
        self.vars[name] = 0

    def run_alloc_float(self, name):
        self.vars[name] = 0.0

    def run_alloc_char(self, name):
        self.vars[name] = ''

    def run_store_int(self, source, target):
        self.vars[target] = self.vars[source]

    run_store_float = run_store_int
    run_store_char = run_store_int

    def run_load_int(self, name, target):
        self.vars[target] = self.vars[name]

    run_load_float = run_load_int
    run_load_char = run_load_int

    def run_sub_int(self, left, right, target):
        self.vars[target] = self.vars[left] - self.vars[right]

    run_sub_float = run_sub_int

    def run_mul_int(self, left, right, target):
        self.vars[target] = self.vars[left] * self.vars[right]

    run_mul_float = run_mul_int

    def run_div_int(self, left, right, target):
        self.vars[target] = self.vars[left] // self.vars[right]

    def run_div_float(self, left, right, target):
        self.vars[target] = self.vars[left] / self.vars[right]

    def run_cmp_int(self, op, left, right, target):
        compare = cmp(self.vars[left], self.vars[right])
        if op == 'lt':
            result = bool(compare < 0)
        elif op == 'le':
            result = bool(compare <= 0)
        elif op == 'eq':
            result = bool(compare == 0)
        elif op == 'ne':
            result = bool(compare != 0)
        elif op == 'ge':
            result = bool(compare >= 0)
        elif op == 'gt':
            result = bool(compare > 0)
        elif op == 'land':
            result = self.vars[left] and self.vars[right]
        elif op == 'lor':
            result = self.vars[left] or self.vars[right]
        self.vars[target] = result

    run_cmp_float = run_cmp_int
    run_cmp_bool = run_cmp_int

    run_print_float = run_print_int
    run_print_char = run_print_int

    def run_call(self, funcname, *args):
        ''' Call a previously declared function. '''
        target = args[-1]
        func = self.vars.get(funcname)
        argvals = [self.vars[name] for name in args[:-1]]
        self.vars[target] = func(*argvals)