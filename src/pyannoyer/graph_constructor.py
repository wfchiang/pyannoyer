import os 
import ast 
import logging 
from typing import List, Dict

from . import model 


LOGGER = logging.getLogger() 


# ==== 
# Evaluation function 
# ====
def evaluation (
    expression, 
    initial_data_flow :model.DataFlow  
): 
    # check parameter(s) 
    assert(isinstance(initial_data_flow, model.DataFlow))

    data_flow = initial_data_flow.clone() 
    tmp_dst_node = None 

    # evaluate the expression 
    if (isinstance(expression, ast.BinOp)): 
        left_source_nodes, data_flow = evaluation(
            expression=expression.left, 
            data_flow=data_flow
        )
        right_source_nodes = evaluation(
            expression=expression.right, 
            data_flow=data_flow
        ) 

        tmp_dst_node = model.Variable.create_temp_variable()
        data_flow.add_assignment(
            operators=[model.Operator('tmp')],             
            src_nodes=(left_source_nodes + right_source_nodes), 
            dst_node=tmp_dst_node
        )

    elif (isinstance(expression, ast.Name) 
          or isinstance(expression, ast.Constant)): 
        tmp_dst_node = data_flow.create_node(ast_node=expression, is_read=True)

    else: 
        LOGGER.warning('[WARNING] Skipping an unsupported expression: {}'.format(ast.dump(expression)))

    # return
    assert(isinstance(tmp_dst_node, model.Node))
    return tmp_dst_node, data_flow  


# ====
# Execution function
# ====
def execution (
    statement, 
    initial_data_flow :model.DataFlow
): 
    # check parameter(s) 
    assert(isinstance(initial_data_flow, model.DataFlow))

    # clond 'data_flow'
    data_flow = initial_data_flow.clone() 
        
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
            data_flow.create_node(ast_node=farg, is_read=True)
            
        # traverse through the function body 
        data_flow = execution(statement=statement.body, initial_data_flow=data_flow)

    elif (isinstance(statement, ast.Assign)): 
        # find out the source node 
        source_nodes = evaluation(expression=statement.value, data_flow=data_flow)
        
        # assign sources to targets 
        for target_node in statement.targets:     
            target_node = data_flow.create_node(ast_node=target_node, is_read=False) 
            data_flow.add_assignment(
                src_nodes=source_nodes, 
                dst_node=target_node 
            )

    elif (isinstance(statement, ast.Return)): 
        source_nodes = evaluation(expression=statement.value, data_flow=data_flow) 

    elif (isinstance(statement, ast.If)): 
        print ('==== True Data Flow ====')
        true_data_flow = execution(statement=statement.body, initial_data_flow=data_flow)
        print(str(true_data_flow))
        
        print('==== False Data Flow ====')
        false_data_flow = execution(statement=statement.orelse, initial_data_flow=data_flow)
        print(str(false_data_flow))

    else:
        LOGGER.warning('[WARNING] Skipping an unsupported statement: {}'.format(ast.dump(statement)))

    # return 
    return data_flow 


# DEBUG DEV ONLY 
dev_source_file_path = '/home/runner/pyannoyer/tests/toy_benchmarks/example1.py'
dev_data_flow = execution(
    statement=dev_source_file_path, 
    initial_data_flow=model.DataFlow() 
) 

print('==== DEV data_flow ====')
print(str(dev_data_flow))

        