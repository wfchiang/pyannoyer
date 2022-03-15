import os 
import ast 
import logging 
from collections import OrderedDict 
from typing import List

LOGGER = logging.getLogger() 


# ====
# "Helper" functions 
# ====
def clone_data_flow (data_flow): 
    new_data_flow = OrderedDict() 
    for k, v in data_flow.items(): 
        new_data_flow[k] = v 
    return new_data_flow 

def append_data_flow (data_flow, additional_data_flow): 
    new_data_flow = clone_data_flow(data_flow=data_flow) 
    for k,v in additional_data_flow.items(): 
        new_data_flow[k] = v 
    return new_data_flow
    
def query_data_source (name_load :ast.Name, data_flow :OrderedDict): 
    # check parameters 
    assert(isinstance(name_load, ast.Name))
    assert(isinstance(data_flow, OrderedDict)) 

    # try to find the data source from 'data_flow'
    data_source = None
    previous_names = list(data_flow.keys()) 
    for i in range(-1, -1*len(previous_names)-1, -1): 
        previous_name_store = previous_names[i] 
        
        if (isinstance(previous_name_store, ast.Name)): 
            if (previous_name_store.id == name_load.id): 
                data_source = previous_name_store 
                break 
        elif (isinstance(previous_name_store, ast.arg)): 
            if (previous_name_store.arg == name_load.id): 
                data_source = previous_name_store 
                break
        else: 
            assert(False), '[ERROR] unsupported previous_name_store: {}'.format(previous_name_store)

    # return 
    return data_source


# ==== 
# "Major" functions 
# ====
def extract_data_flow (
    source, initial_data_flow :OrderedDict
): 
    # check parameter(s) 
    assert(isinstance(initial_data_flow, OrderedDict))

    # clond 'data_flow'
    data_flow = clone_data_flow(data_flow=initial_data_flow) 
    eval_nodes = [] 
        
    # capture the AST node (source) from file 
    if (type(source) is str): 
        # check the source file path 
        assert(os.path.isfile(source)), f'[ERROR] source file does not exist: {source}'
        # load the ast module from a file 
        with open(source, 'r') as source_file: 
            source = ast.parse(source_file.read()) 

    # walk through the AST node
    if (isinstance(source, List)): 
        for statement in source: 
            _, data_flow = extract_data_flow(source=statement, initial_data_flow=data_flow)
            
    elif (isinstance(source, ast.Module)):
        _, data_flow = extract_data_flow(source=source.body, initial_data_flow=data_flow)

    elif (isinstance(source, ast.FunctionDef)): 
        # add the function arguments into data_flow as "untracked" (None) (for now...) 
        func_args = source.args.args 
        for farg in func_args: 
            data_flow[farg] = [None]
        # traverse through the function body 
        _, data_flow = extract_data_flow(source=source.body, initial_data_flow=data_flow)

    elif (isinstance(source, ast.Assign)): 
        # find out the source node 
        source_nodes, data_flow = extract_data_flow(source=source.value, initial_data_flow=data_flow)
        
        # assign sources to targets 
        for target_node in source.targets:     
            data_flow[target_node] = source_nodes 

    elif (isinstance(source, ast.BinOp)): 
        left_source_nodes, data_flow = extract_data_flow(source=source.left, initial_data_flow=data_flow)
        right_source_nodes, data_flow = extract_data_flow(source=source.right, initial_data_flow=data_flow) 
        eval_nodes = left_source_nodes + right_source_nodes

    elif (isinstance(source, ast.Return)): 
        _, data_flow = extract_data_flow(source=source.value, initial_data_flow=data_flow) 

    elif (isinstance(source, ast.Name)): 
        eval_nodes.append(query_data_source(name_load=source, data_flow=data_flow))
        
    elif (isinstance(source, ast.Constant)): 
        eval_nodes.append(source)

    elif (isinstance(source, ast.If)): 
        true_data_flow = clone_data_flow(data_flow) 
        _, true_data_flow = extract_data_flow(source=source.body, initial_data_flow=true_data_flow)

        print ('==== True Data Flow ====')
        for k, v in true_data_flow.items(): 
            print('{} : {}'.format(k, v))

        false_data_flow = clone_data_flow(data_flow)
        _, false_data_flow = extract_data_flow(source=source.orelse, initial_data_flow=false_data_flow)

        print('==== False Data Flow ====')
        for k, v in false_data_flow.items(): 
            print('{} : {}'.format(k, v))

    else:
        LOGGER.warning('[WARNING] Skipping an unsupported AST node: {}'.format(ast.dump(source)))

    # return 
    return eval_nodes, data_flow 


# DEBUG DEV ONLY 
dev_source_file_path = '/home/runner/pyannoyer/tests/toy_benchmarks/example0.py'
_, dev_data_flow = extract_data_flow(
    source=dev_source_file_path, 
    initial_data_flow=OrderedDict()
) 

print('==== DEV data_flow ====')
for k,v in dev_data_flow.items(): 
    print('{} : {}'.format(k, v))

        