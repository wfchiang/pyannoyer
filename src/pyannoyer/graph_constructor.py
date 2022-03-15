import os 
import ast 
import logging 
from collections import OrderedDict 

LOGGER = logging.getLogger() 


# ====
# "Helper" functions 
# ====
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
        else: 
            assert(False), '[ERROR] unsupported previous_name_store: {}'.format(previous_name_store)

    # return 
    return data_source


# ==== 
# "Major" functions 
# ====
# IMPORTANT: this function will cause side effects on 'data_flow' 
def extract_data_flow (source, data_flow :OrderedDict): 
    # check parameter(s) 
    assert(isinstance(data_flow, OrderedDict))
        
    # capture the AST node (source) from file 
    if (type(source) is str): 
        # check the source file path 
        assert(os.path.isfile(source)), f'[ERROR] source file does not exist: {source}'
        # load the ast module from a file 
        with open(source, 'r') as source_file: 
            source = ast.parse(source_file.read()) 

    # walk through the AST node
    eval_nodes = [] 
    if (isinstance(source, ast.Module)):
        for ast_sub_node in source.body: 
            extract_data_flow(source=ast_sub_node, data_flow=data_flow)

    elif (isinstance(source, ast.FunctionDef)): 
        for ast_sub_node in source.body: 
            extract_data_flow(source=ast_sub_node, data_flow=data_flow)

    elif (isinstance(source, ast.Assign)): 
        print('--')
        print(ast.dump(source))
        # find out the source node 
        source_nodes = extract_data_flow(source=source.value, data_flow=data_flow)
        
        # assign sources to targets 
        for target_node in source.targets: 
            print('== Assign ==')
            print(target_node)
            for sn in source_nodes: 
                print('    {}'.format(sn))
                
            data_flow[target_node] = source_nodes 

    elif (isinstance(source, ast.BinOp)): 
        eval_nodes += extract_data_flow(source=source.left, data_flow=data_flow)
        eval_nodes += extract_data_flow(source=source.right, data_flow=data_flow) 

    elif (isinstance(source, ast.Return)): 
        return extract_data_flow(source=source.value, data_flow=data_flow) 

    elif (isinstance(source, ast.Name)): 
        eval_nodes.append(query_data_source(name_load=source, data_flow=data_flow))
        
    elif (isinstance(source, ast.Constant)): 
        eval_nodes.append(source)

    else:
        # DEBUG 
        print('----')
        print(ast.dump(source))
        
        LOGGER.warning('[WARNING] Skipping an unsupported AST node: {}'.format(source))

    # return 
    return eval_nodes 


# DEBUG DEV ONLY 
dev_source_file_path = '/home/runner/pyannoyer/tests/toy_benchmarks/example0.py'
dev_data_flow = OrderedDict() 
data_flow_graph = extract_data_flow(
    source=dev_source_file_path, 
    data_flow=dev_data_flow
) 

print('==== DEV data_flow ====')
for k,v in dev_data_flow.items(): 
    print('{} : {}'.format(k, v))

        