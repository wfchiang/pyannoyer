from typing import List, Dict 
import json 

import ast 


# ====
# Classes
# ====
class Node (object): 
    def __init__ (self): 
        pass 


class Constant (Node): 
    def __init__ (self, value): 
        self.value = value 


class Variable (Node): 
    def __init__ (self, name :str, stamp :int): 
        self.name = name 
        self.stamp = stamp 


class Assignment (object): 
    def __init__ (self, src :List[Node], dst :Variable): 
        assert(isinstance(dst, Variable))
        assert(isinstance(src, List) and all([isinstance(n, Node) for n in src])) 

        self.src = src 
        self.dst = dst 


class DataFlow (object): 
    def __init__ (self): 
        self.assignments = [] 
        self.latest_var_stamp = {} 
        
    def create_node (self, ast_node, is_read :bool):
        node_name = None 
        if (isinstance(ast_node, ast.Name)): 
            node_name = ast_node.id 
        elif (isinstance(ast_node, ast.arg)):
            node_name = ast_node.arg 
        elif (isinstance(ast_node, ast.Constant)): 
            assert(is_read), '[ERROR] can only create constant nodes under is_real=True'
            return Constant(value=None)
        else: 
            assert(False), '[ERROR] unsupported AST node type'
            
        if (node_name not in self.latest_var_stamp): 
            self.latest_var_stamp[node_name] = 0 
            return Variable(name=node_name, stamp=0)
        else: 
            node_stamp = self.latest_var_stamp[node_name]
            node_stamp = (node_stamp if is_read else node_stamp+1)
            self.latest_var_stamp[node_name] = node_stamp
            return Variable(name=node_name, stamp=node_stamp)
        
            

    def add_assignment (self, src_node, dst_nodes :List[ast.Node]): 
        assert(isins)
        if (isinstance(_ast_node, ast.arg)): 
            _node_name = _ast_node.arg 
        elif (isinstance(_ast_node, ast.Name)): 
            _node_name = _ast_node.id 
        elif (isinstance(_ast_node, ast.Constant)): 
            return '__constant__'


# ====
# OLD STUFFS 
# ====




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

    def _set_var_type (self, space :Dict, var :str, var_type): 
        assert(isinstance(var, str))
        assert(var in space)
        assert(isinstance(space[var], StoredValue))
        assert(isinstance(space[var].metadata, Dict))

        space[var].metadata['type'] = var_type 

    def _get_var_type (self, space :Dict, var :str): 
        assert(isinstance(var, str))
        assert(var in space)
        assert(isinstance(space[var], StoredValue))
        assert(isinstance(space[var].metadata, Dict))

        return (None if ('type' not in space[var].metadata) else space[var].metadata['type'])

    def set_store_var_type (self, var :str, var_type): 
        self._set_var_type(
            space=self.store, 
            var=var, 
            var_type=var_type
        )
        
    def get_store_var_type (self, var :str): 
        return self._get_var_type(
            space=self.store, 
            var=var
        )