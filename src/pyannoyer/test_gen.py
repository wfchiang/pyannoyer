from typing import Callable 

class TestGenOperation (object): 
    def __init__ (self, label :str, f :Callable): 
        assert(type(label) is str)
        assert(isinstance(f, Callable))
        self.label = label 
        self.opt = f  

class TestGen (object): 
    def __init__ (self): 
        self.operations = [] 

    def add_operation (self, label :str, f :Callable): 
        self.operations.append(TestGenOperation(label=label, f=f))

    def generate (self): 
        v = None 
        for opt in self.operations: 
            assert(isinstance(opt, TestGenOperation))
            v = opt.f(v) 
        return v 