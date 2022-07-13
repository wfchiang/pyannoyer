import os 
import ast 
import logging 
from typing import List, Dict 

from . import static_analysis as SA 


LOGGER = logging.getLogger() 


# ==== 
# Evaluation function 
# ====
def evaluation (
    expression, 
    initial_data_flow :SA.DataFlow  
): 
    # check parameter(s) 
    assert(isinstance(initial_data_flow, SA.DataFlow))

    data_flow = initial_data_flow.clone() 
    tmp_dst_node = None 

    # evaluate the expression 
    if (isinstance(expression, ast.BinOp)): 
        left_source_node, data_flow = evaluation(
            expression=expression.left, 
            initial_data_flow=data_flow
        )
        right_source_node, data_flow = evaluation(
            expression=expression.right, 
            initial_data_flow=data_flow
        ) 

        tmp_dst_node = data_flow.create_temp_variable() 
        
        data_flow.add_assignment(
            operators=[SA.Operator(ast.dump(expression.op))],             
            src_nodes=[left_source_node, right_source_node], 
            dst_node=tmp_dst_node
        )

    elif (isinstance(expression, ast.Name) 
          or isinstance(expression, ast.Constant)): 
        tmp_dst_node = data_flow.create_node(ast_node=expression, is_read=True)

    else: 
        LOGGER.warning('[WARNING] set "unbounded" as the evaluation result for the unsupported expression: {}'.format(ast.dump(expression)))
        tmp_dst_node = SA.Unbounded() 

    # return
    assert(isinstance(tmp_dst_node, SA.Node))
    return tmp_dst_node, data_flow  


# ====
# Execution function
# ====
def execution (
    statement, 
    initial_data_flow :SA.DataFlow
): 
    # check parameter(s) 
    assert(isinstance(initial_data_flow, SA.DataFlow))

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
        source_node, data_flow = evaluation(expression=statement.value, initial_data_flow=data_flow)
        
        # assign sources to targets 
        for target_node in statement.targets:     
            target_node = data_flow.create_node(ast_node=target_node, is_read=False) 
            data_flow.add_assignment(
                operators=[SA.Operator.create_assign()], 
                src_nodes=[source_node], 
                dst_node=target_node 
            )

    elif (isinstance(statement, ast.Return)): 
        source_node, data_flow = evaluation(expression=statement.value,initial_data_flow=data_flow) 

    elif (isinstance(statement, ast.If)): 
        true_data_flow = execution(statement=statement.body, initial_data_flow=data_flow)
        
        false_data_flow = execution(statement=statement.orelse, initial_data_flow=data_flow)

        # merge the 2 branches 
        data_flow = SA.DataFlow.merge(true_data_flow, false_data_flow)

    else:
        LOGGER.warning('[WARNING] Skipping an unsupported statement: {}'.format(ast.dump(statement)))

    # return 
    return data_flow 


# DEBUG DEV ONLY 
if __name__ == '__main__': 
    import sys 
    assert(len(sys.argv) >= 2)
    
    dev_source_file_path = sys.argv[1] 
    assert(os.path.isfile(dev_source_file_path))
    
    dev_data_flow = execution(
        statement=dev_source_file_path, 
        initial_data_flow=SA.DataFlow() 
    ) 
    
    print('==== Data Flow ====')
    print(str(dev_data_flow))

    print('==== Variable Lineup ====')
    for i, v in enumerate(dev_data_flow.vars_lineup): 
        print(f'{i} : {v}')

    print('==== Data Flow Matrix ====')
    dataflow_matrix = SA.create_dataflow_matrix(dev_data_flow)
    print(dataflow_matrix)

        