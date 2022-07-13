from abc import ABC, abstractmethod 
from typing import List, Dict 
import json 
import ast 
import numpy as np 


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


class Unbounded (Node): 
    NAME = '__unbounded__'
    def __init__ (self): 
        pass 

    def clone (self): 
        return Unbounded() 

    def __str__ (self): 
        return str((Unbounded.NAME, None))
        

class Constant (Node): 
    NAME = '__const__'
    
    def __init__ (self, value): 
        self.value = value 

    def clone (self): 
        return Constant(value=self.value)  

    def __str__ (self): 
        return str((Constant.NAME, self.value))


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

    def __eq__ (self, other):
        if (isinstance(other, Variable)): 
            if (self.name == other.name): 
                if (self.stamp == other.stamp): 
                    if (len(self.labels) == len(other.labels)): 
                        return all([(sl==ol) for sl, ol in zip(self.labels, other.labels)])

        return False 

    def __str__ (self): 
        return str((self.name, self.stamp, self.labels))

    def add_label (self, lab :str): 
        assert(type(lab) is str) 

        if (lab not in self.labels): 
            self.labels.append(lab) 

    def is_temp_variable (self): 
        return self.name == Variable.TEMP_VAR_NAME 


class Operator (object): 
    PHI_NAME = '__phi()__'
    ASSIGN_NAME = '__assign()__'
    
    def __init__ (self, name :str): 
        self.name = name 

    def clone (self): 
        return Operator(name=self.name) 

    def __str__ (self): 
        return self.name 

    @classmethod 
    def create_phi (cls): 
        return cls(name=Operator.PHI_NAME) 

    @classmethod 
    def create_assign (cls): 
        return cls(name=Operator.ASSIGN_NAME)


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
        self.vars_lineup = [] # This is for lis
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
            v = Variable(name=node_name, stamp=node_stamp)
            self.vars_lineup.append(v) 
            return v 
        else: 
            is_first_read = (node_name not in self.latest_var_stamp)
            
            if (is_first_read): 
                self.latest_var_stamp[node_name] = 0 
            
            node_stamp = self.latest_var_stamp[node_name]
            v = Variable(name=node_name, stamp=node_stamp) 

            if (is_first_read): 
                self.vars_lineup.append(v) 
            
            return v

    def create_temp_variable (self): 
        tmp_var = Variable('', 0) # just give a temporary name and stamp 
        tmp_var.name = Variable.TEMP_VAR_NAME
        tmp_var.stamp = VarStamper.next(tmp_var.name)

        if (tmp_var not in self.vars_lineup): 
            self.vars_lineup.append(tmp_var)
            
        return tmp_var 

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
        cloned_dataflow.vars_lineup = [v.clone() for v in self.vars_lineup]
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
        
        merged_data_flow.vars_lineup = [v.clone() for v in data_flow_0.vars_lineup]
        for v in data_flow_1.vars_lineup: 
            if (v not in merged_data_flow.vars_lineup): 
                merged_data_flow.vars_lineup.append(v) 

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
# Matrix Creation Functions 
# ====    
def create_dataflow_matrix (data_flow): 
    assert(isinstance(data_flow, DataFlow)) 
    assert(len(data_flow.vars_lineup) > 0)

    # init the dst-to-src matrix (dst_src) 
    n_vars = len(data_flow.vars_lineup)
    dst_src = np.zeros((n_vars, n_vars)).astype(np.int32)
    for i in range(0, n_vars): 
        dst_src[i][i] = 1 

    # set the dataflow matrx 
    for asgn in data_flow.assignments: 
        i_dst = data_flow.vars_lineup.index(asgn.dst)
        assert(i_dst >= 0)
        
        for src in asgn.src: 
            if (isinstance(src, Variable)): 
                i_src = data_flow.vars_lineup.index(src) 
                assert(i_src >= 0)
                
                dst_src[i_dst][i_src] = 1

    # return 
    return dst_src 
    

def create_node_feature_matrix (data_flow): 
    assert(isinstance(data_flow, DataFlow))