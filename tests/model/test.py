import unittest 
import ast 
from typing import List 

import pyannoyer.model as model 

class Test (unittest.TestCase): 
    def test_Context_0 (self): 
        ctx = model.Context() 

        ctx.write_store('int_0', 1)
        self.assertEqual(1, ctx.read_store('int_0'))

        