from typing import List 
import ast 

from .model import Context 
from .ast_utils import getters

def flatten_expr (expr, ctx :Context): 
    if (isinstance(expr, ast.Constant)): 
        return expr 

    elif (isinstance(expr, ast.Name)): 
        var_id = expr.id 
        return ctx.read_store(var_id)

    elif (isinstance(expr, ast.BinOp)): 
        expr.left = flatten_expr(expr.left, ctx=ctx)
        expr.right = flatten_expr(expr.right, ctx=ctx)
        return expr 

    elif (isinstance(expr, ast.Return)): 
        return expr 

    else: 
        assert(False), '[Error] unknown type {} of expr {}'.format(type(expr), ast.dump(expr))

def run_func_def (ast_func_def :ast.FunctionDef):
    assert(isinstance(ast_func_def, ast.FunctionDef)) 

    # Initialize the context
    init_ctx = Context() 

    # Find the arguments of the function 
    func_args = ast_func_def.args.args
    for fa in func_args: 
        assert(isinstance(fa, ast.arg))
        fa_name = fa.arg
        fa_anno = fa.annotation 
        init_val = ast.Constant(None)  
        init_ctx.write_store(var=fa_name, val=init_val)

    # Load the function body 
    init_ctx.operations = ast_func_def.body

    running_contexts = [init_ctx]
    terminated_contexts = [] 

    # "Execute" on of the running context 
    while (len(running_contexts) > 0): 
        curr_ctx = running_contexts[0]
        running_contexts = running_contexts[1:]

        # If no more ast-node to visit... 
        if (len(curr_ctx.operations) == 0): 
            terminated_contexts.append(curr_ctx)
            
        # Visit the next ast-node 
        else: 
            next_ctx = curr_ctx.clone() 
            next_ctx.operations = next_ctx.operations[1:]
            curr_ast_node = curr_ctx.operations[0]

            if (isinstance(curr_ast_node, ast.Assign)): 
                targets = curr_ast_node.targets 
                assert(isinstance(targets, list))
                assert(len(targets) == 1), '[Error] currently, we only support len(targets) == 1'

                target = targets[0]
                assert(isinstance(target, ast.Name))
                target_id = target.id

                expr = flatten_expr(curr_ast_node.value, next_ctx) 
                next_ctx.write_store(target_id, expr)

                running_contexts.append(next_ctx)

                print('<<<<<<<<')
                print('inst')
                print(ast.dump(curr_ast_node))
                print('targets')
                for t in targets: 
                    print(ast.dump(t))
                print('expr')
                print(ast.dump(expr))
                print('>>>>>>>>')

            elif (isinstance(curr_ast_node, ast.Return)): 
                print('Return...')

            else: 
                pass 
                print('[ERROR] unsupported AST node: {}'.format(ast.dump(curr_ast_node)))
                print(f'[ERROR] Context: {curr_ctx}')
                assert(False), f'[ERROR] unsupported AST node: {curr_ast_node}'
