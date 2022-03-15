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
# Evaluation function 
# ====
def evaluation (
    expression, data_flow :OrderedDict 
): 
    # check parameter(s) 
    assert(isinstance(data_flow, OrderedDict))

    eval_nodes = [] 

    # evaluate the expression 
    if (isinstance(expression, ast.BinOp)): 
        left_source_nodes = evaluation(
            expression=expression.left, 
            data_flow=data_flow
        )
        right_source_nodes = evaluation(
            expression=expression.right, 
            data_flow=data_flow
        ) 
        eval_nodes = left_source_nodes + right_source_nodes 

    elif (isinstance(expression, ast.Name)): 
        eval_nodes.append(query_data_source(name_load=expression, data_flow=data_flow))

    elif (isinstance(expression, ast.Constant)): 
        eval_nodes.append(expression)

    else: 
        LOGGER.warning('[WARNING] Skipping an unsupported expression: {}'.format(ast.dump(expression)))

    # return 
    return eval_nodes 


# ====
# Execution function
# ====
def execution (
    statement, initial_data_flow :OrderedDict
): 
    # check parameter(s) 
    assert(isinstance(initial_data_flow, OrderedDict))

    # clond 'data_flow'
    data_flow = clone_data_flow(data_flow=initial_data_flow) 
        
    # capture the AST node (statement) from file 
    if (type(statement) is str): 
        # check the source file path 
        assert(os.path.isfile(statement)), f'[ERROR] source file does not exist: {statement}'
        # load the ast module from a file 
        with open(statement, 'r') as source_file: 
            statement = ast.parse(source_file.read()) 

    # walk through the AST node
    if (isinstance(statement, List)): 
        for stat in statement: 
            data_flow = execution(statement=stat, initial_data_flow=data_flow)
            
    elif (isinstance(statement, ast.Module)):
        data_flow = execution(statement=statement.body, initial_data_flow=data_flow)

    elif (isinstance(statement, ast.FunctionDef)): 
        # add the function arguments into data_flow as "untracked" (None) (for now...) 
        func_args = statement.args.args 
        for farg in func_args: 
            data_flow[farg] = [None]
        # traverse through the function body 
        data_flow = execution(statement=statement.body, initial_data_flow=data_flow)

    elif (isinstance(statement, ast.Assign)): 
        # find out the source node 
        source_nodes = evaluation(expression=statement.value, data_flow=data_flow)
        
        # assign sources to targets 
        for target_node in statement.targets:     
            data_flow[target_node] = source_nodes 

    elif (isinstance(statement, ast.Return)): 
        source_nodes = evaluation(expression=statement.value, data_flow=data_flow) 

    elif (isinstance(statement, ast.If)): 
        true_data_flow = execution(statement=statement.body, initial_data_flow=data_flow)

        print ('==== True Data Flow ====')
        for k, v in true_data_flow.items(): 
            print('{} : {}'.format(k, v))

        false_data_flow = execution(statement=statement.orelse, initial_data_flow=data_flow)

        print('==== False Data Flow ====')
        for k, v in false_data_flow.items(): 
            print('{} : {}'.format(k, v))

    else:
        LOGGER.warning('[WARNING] Skipping an unsupported statement: {}'.format(ast.dump(statement)))

    # return 
    return data_flow 


# DEBUG DEV ONLY 
dev_source_file_path = '/home/runner/pyannoyer/tests/toy_benchmarks/example0.py'
dev_data_flow = execution(
    statement=dev_source_file_path, 
    initial_data_flow=OrderedDict()
) 

print('==== DEV data_flow ====')
for k,v in dev_data_flow.items(): 
    print('{} : {}'.format(k, v))

        