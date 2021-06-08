import unittest 
import ast 
from typing import List 
from . import example

class Test (unittest.TestCase): 
    def test_0 (self):
        # Load the module 
        exp_mod = None 
        with open(example.__file__, 'r') as exp_file: 
            exp_mod = ast.parse(exp_file.read())
        self.assertIsInstance(exp_mod, ast.Module)

        # Get the function we are looking format
        exp_body = exp_mod.body 
        self.assertIsInstance(exp_body, List)

        foo_func = exp_body[0]
        self.assertIsInstance(foo_func, ast.FunctionDef)

        # Collect the function argument names 
        foo_func_arg_names = [arg.arg for arg in foo_func.args.args ]
        self.assertTrue(
            all([type(n) is str for n in foo_func_arg_names])
        )

        