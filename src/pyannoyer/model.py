from typing import List, Dict 
import json 

import ast 

TYPES = [int, float, str, list]

# ====
# Classes 
# ====
class StoredValue (object): 
    def __init__ (self, expr, metadata :Dict): 
        assert(isinstance(metadata, Dict)) 

        self.expr = expr 
        self.metadata = metadata 

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
        
        metadata = ({} if (var not in self.store) else self.store[var].metadata)
        self.store[var] = StoredValue(
            expr=val, 
            metadata=metadata 
        )

    def read_store (self, var :str): 
        assert(isinstance(var, str))
        assert(var in self.store)
        return self.store[var]
        