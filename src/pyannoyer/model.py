from abc import ABC, abstractmethod 
from typing import List, Dict 
import json 
import ast 


# ====
# Classes
# ====
class VarStamper (object): 
    var_stamp = {} 

    @classmethod
    def next(cls, var_name :str): 
        if (var_name not in cls.var_stamp): 
            cls.var_stamp[var_name] = 1
        print('[DEBUG] {} {}'.format(var_name, cls.var_stamp[var_name]))
        cls.var_stamp[var_name] = cls.var_stamp[var_name] + 1
        return cls.var_stamp[var_name] - 1 
    
class Node (ABC):
    @abstractmethod 
    def clone (self): 
        pass 

    @abstractmethod 
    def __str__ (self): 
        pass 
        

class Constant (Node): 
    def __init__ (self, value): 
        self.value = value 

    def clone (self): 
        return Constant(value=self.value)  

    def __str__ (self): 
        return str(('__const__', self.value))


class Variable (Node): 
    def __init__ (self, name :str, stamp :int): 
        self.name = name 
        self.stamp = stamp 

    def clone (self): 
        return Variable(name=self.name, stamp=self.stamp) 

    def __str__ (self): 
        return str((self.name, self.stamp))


class Assignment (object): 
    def __init__ (self, src :List[Node], dst :Variable): 
        assert(isinstance(dst, Variable))
        assert(isinstance(src, List) and all([isinstance(n, Node) for n in src])) 

        self.src = src 
        self.dst = dst 

    def clone (self): 
        return Assignment(
            src=[s.clone() for s in self.src], 
            dst=self.dst.clone()  
        )

    def __str__ (self): 
        return '{} <- {}'.format(
            str(self.dst), 
            ' '.join([str(s) for s in self.src])
        )


class DataFlow (object): 
    def __init__ (self): 
        self.assignments = [] 
        self.latest_var_stamp = {} 
        
    def create_node (
        self, 
        ast_node, 
        is_read :bool
    ):
        # Extract the node name 
        node_name = None 
        if (isinstance(ast_node, ast.Name)): 
            node_name = ast_node.id 
        elif (isinstance(ast_node, ast.arg)):
            node_name = ast_node.arg 
        elif (isinstance(ast_node, ast.Constant)): 
            assert(is_read), '[ERROR] can only create constant nodes under is_real=True'
            return Constant(value=None)
        else: 
            assert(False), '[ERROR] unsupported AST node type: {}'.format(ast_node)

        # Create the node 
        if (not is_read): 
            node_stamp = VarStamper.next(node_name) 
            self.latest_var_stamp[node_name] = node_stamp 
            return Variable(name=node_name, stamp=node_stamp)
        else: 
            if (node_name not in self.latest_var_stamp): 
                self.latest_var_stamp[node_name] = 0 
            node_stamp = self.latest_var_stamp[node_name]
            return Variable(name=node_name, stamp=node_stamp)

    def add_assignment (
        self, 
        src_nodes :List[Node], 
        dst_node :Node 
    ): 
        assert(all([isinstance(sn, Node) for sn in src_nodes]))
        assert(isinstance(dst_node, Node))
        
        self.assignments.append(
            Assignment(
                src=src_nodes, 
                dst=dst_node 
            )
        )

    def clone (self): 
        cloned_dataflow = DataFlow() 
        cloned_dataflow.assignments = [asm.clone() for asm in self.assignments]
        cloned_dataflow.latest_var_stamp = json.loads(json.dumps(self.latest_var_stamp))
        return cloned_dataflow 

    def __str__ (self): 
        return '\n'.join([str(asm) for asm in self.assignments])

        
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