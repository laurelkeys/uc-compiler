import os
import sys

from collections import defaultdict

import uC_ops
from uC_AST import NodeVisitor

###########################################################
## uC Intermediate Representation (IR) ####################
###########################################################

class GenerateCode(NodeVisitor):
    ''' Node visitor class that creates 3-address encoded instruction sequences. '''

    def __init__(self):
        super(GenerateCode, self).__init__()
        self.versions = defaultdict(int) # version dictionary for temporaries
        self.code = [] # generated code as a list of tuples

    def new_temp(self, typeobj):
        ''' Create a new temporary variable of a given type. '''
        name = "t_%d" % (self.versions[typeobj.name])
        self.versions[typeobj.name] += 1
        return name

    # NOTE A few sample methods follow. You may have to adjust
    #      depending on the names of the AST nodes you've defined

    def visit_Literal(self, node):
        # Create a new temporary variable name
        target = self.new_temp(node.type)

        # Make the SSA opcode and append to list of generated instructions
        inst = (f'literal_{node.type.name}', node.value, target)
        self.code.append(inst)

        # Save the name of the temporary variable where the value was placed
        node.gen_location = target

    def visit_BinaryOp(self, node):
        # Visit the left and right expressions
        self.visit(node.left)
        self.visit(node.right)

        # Make a new temporary for storing the result
        target = self.new_temp(node.type)

        # Create the opcode and append to list
        opcode = binary_ops[node.op] + "_"+node.left.type.name
        inst = (opcode, node.left.gen_location, node.right.gen_location, target)
        self.code.append(inst)

        # Store location of the result on the node
        node.gen_location = target

    def visit_PrintStatement(self, node):
        # Visit the expression
        self.visit(node.expr)

        # Create the opcode and append to list
        inst = ('print_'+node.expr.type.name, node.expr.gen_location)
        self.code.append(inst)

    def visit_VarDeclaration(self, node):
        # allocate on stack memory
        inst = ('alloc_'+node.type.name,
                    node.id)
        self.code.append(inst)
        # store optional init val
        if node.value:
            self.visit(node.value)
            inst = ('store_'+node.type.name,
                    node.value.gen_location,
                    node.id)
            self.code.append(inst)

    def visit_LoadLocation(self, node):
        target = self.new_temp(node.type)
        inst = ('load_'+node.type.name,
                node.name,
                target)
        self.code.append(inst)
        node.gen_location = target

    def visit_AssignmentStatement(self, node):
        self.visit(node.value)
        inst = ('store_'+node.value.type.name,
                node.value.gen_location,
                node.location)
        self.code.append(inst)

    def visit_UnaryOp(self, node):
        self.visit(node.left)
        target = self.new_temp(node.type)
        opcode = unary_ops[node.op] + "_" + node.left.type.name
        inst = (opcode, node.left.gen_location)
        self.code.append(inst)
        node.gen_location = target

    # TODO Implement `visit_<>` methods for all of the other AST nodes.
    #      Make instructions and append them to the `self.code` list.