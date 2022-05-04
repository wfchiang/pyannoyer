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
    TEMP_VAR_NAME = '__tmp_var__'
    
    def __init__ (self, name :str, stamp :int): 
        assert(name != Variable.TEMP_VAR_NAME)
        
        self.name = name 
        self.stamp = stamp 
        self.labels = [] 

    def clone (self): 
        cloned_var = Variable(name='', stamp='')
        cloned_var.name = self.name 
        cloned_var.stamp = self.stamp
        cloned_var.labels = [lab for lab in self.labels]
        return cloned_var 

    def __str__ (self): 
        return str((self.name, self.stamp, self.labels))

    def add_label (self, lab :str): 
        assert(type(lab) is str) 

        if (lab not in self.labels): 
            self.labels.append(lab) 

    @classmethod 
    def create_temp_variable (cls): 
        tmp_var = Variable('', 0) # just give a temporary name and stamp 
        tmp_var.name = Variable.TEMP_VAR_NAME
        tmp_var.stamp = VarStamper.next(tmp_var.name)
        return tmp_var 

    def is_temp_variable (self): 
        return self.name == Variable.TEMP_VAR_NAME 


class Operator (object): 
    def __init__ (self, name :str): 
        self.name = name 

    def clone (self): 
        return Operator(name=self.name) 

    def __str__ (self): 
        return self.name 

    @classmethod 
    def create_phi (cls): 
        return cls(name='__phi()__') 

    @classmethod 
    def create_assign (cls): 
        return cls(name='__assign()__')


class Assignment (object): 
    def __init__ (
        self, 
        ops :List[Operator], 
        src :List[Node], 
        dst :Variable
    ): 
        assert(isinstance(dst, Variable))
        assert(isinstance(ops, List) and all([isinstance(n, Operator) for n in ops]))
        assert(isinstance(src, List) and all([isinstance(n, Node) for n in src])) 

        self.src = src 
        self.ops = ops 
        self.dst = dst 

    def clone (self): 
        return Assignment(
            src=[s.clone() for s in self.src], 
            ops=[o.clone() for o in self.ops], 
            dst=self.dst.clone()  
        )

    def __str__ (self): 
        return '{} <- {} : {}'.format(
            str(self.dst), 
            ' '.join([str(o) for o in self.ops]), 
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
        if (type(ast_node) is str): 
            node_name = ast_node 
        elif (isinstance(ast_node, ast.Name)): 
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
        operators :List[Operator], 
        src_nodes :List[Node], 
        dst_node :Node 
    ): 
        assert(all([isinstance(sn, Node) for sn in src_nodes]))
        assert(isinstance(dst_node, Node))
        
        self.assignments.append(
            Assignment(
                ops=operators, 
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

    @classmethod 
    def merge (cls, data_flow_0, data_flow_1): 
        assert(isinstance(data_flow_0, cls))
        assert(isinstance(data_flow_1, cls))

        # join the variables 
        vars_0 = set(data_flow_0.latest_var_stamp.keys()) 
        vars_1 = set(data_flow_1.latest_var_stamp.keys())
        all_vars = vars_0.union(vars_1) 

        # init the data flow 
        merged_data_flow = cls() 
        merged_data_flow.assignments = data_flow_0.assignments + data_flow_1.assignments 

        # create phi nodes for variables 
        for var in all_vars: 
            if (var in vars_0 and var in vars_1): 
                merged_data_flow.latest_var_stamp[var] = max(
                    data_flow_0.latest_var_stamp[var], 
                    data_flow_1.latest_var_stamp[var]
                )
                merged_data_flow.add_assignment(
                    operators=[Operator.create_phi()], 
                    src_nodes=[
                        data_flow_0.create_node(ast_node=var, is_read=True), 
                        data_flow_1.create_node(ast_node=var, is_read=True)
                    ], 
                    dst_node=merged_data_flow.create_node(ast_node=var, is_read=False)
                )
                
            elif (var in vars_0 and var not in vars_1): 
                merged_data_flow.latest_var_stamp[var] = data_flow_0.latest_var_stamp[var] 
                merged_data_flow.add_assignment(
                    operators=[Operator.create_assign()], 
                    src_nodes=[data_flow_0.create_node(ast_node=var, is_read=True)], 
                    dst_node=merged_data_flow.create_node(ast_node=var, is_read=False)
                )
                
            elif (var not in vars_0 and var in vars_1): 
                merged_data_flow.latest_var_stamp[var] = data_flow_1.latest_var_stamp[var] 
                merged_data_flow.add_assignment(
                    operators=[Operator.create_assign], 
                    src_nodes=[data_flow_1.create_node(ast_node=var, is_read=True)], 
                    dst_node=merged_data_flow.create_node(ast_node=var, is_read=False)
                )
                
            else: 
                assert(False) 

        # return 
        return merged_data_flow 

        
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