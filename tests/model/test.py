import unittest 
import ast 
from typing import List 

import pyannoyer.model as model 

class Test (unittest.TestCase): 
    def test_Context_0 (self): 
        ctx = model.Context() 

        ctx.write_store('int_0', 1)
        stored_v = ctx.read_store('int_0')
        self.assertEqual(1, stored_v.expr)

    def test_Context_1 (self):
        ctx = model.Context() 

        ctx.write_store('str_0', 'hi')
        ctx.set_store_var_type('str_0', str)
        stored_v = ctx.read_store('str_0')
        self.assertEqual('hi', stored_v.expr)
        self.assertTrue(isinstance(
            stored_v.expr, 
            ctx.get_store_var_type('str_0')
        ))

        