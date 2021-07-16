from typing import List
import json 

import ast 

TYPES = [int, float, str, list]

# ====
# Classes 
# ====
class Context (object): 
    def __init__ (self): 
        self.heap = [] 
        self.store = {} 
        self.operations = []

    def clone (self): 
        new_ctx = Context() 

        new_ctx.heap = self.heap[:]
        
        for k, v in self.store.items(): 
            new_ctx.store[k] = v 

        new_ctx.operations = self.operations[:]

        return new_ctx

    def write_store (self, var :str, val): 
        assert(isinstance(var, str))
        
        self.store[var] = val

    def read_store (self, var :str): 
        assert(isinstance(var, str))
        assert(var in self.store)
        return self.store[var]
        