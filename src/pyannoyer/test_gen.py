from typing import List 
import ast 
import json 

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

    def __str__ (self): 
        return json.dumps(
            {
                'heap': self.heap, 
                'store': self.store, 
                'operations': [str(opt) for opt in self.operations]
            }, 
            indent=4
        )

def run_expr (ast_expr :ast.Expr, prev_ctx :Context):
    ctx = prev_ctx.clone() 

    if (isinstance(ast_expr, ast.Constant)):
        ctx.heap[0] = ast_expr.value 

    elif (isinstance(ast_expr, ast.Name)): 
        assert(ast_expr.id in ctx), f'[ERROR] name {ast_expr.id} missed in the store'
        ctx.heap[0] = ctx.store[ast_expr.id]
    
    else: 
        print('[ERROR] unsupported AST expr: {}'.format(ast.dump(ast_expr)))
        print(f'[ERROR] Context: {ctx}')
        assert(False), f'[ERROR] unsupport AST expr: {ast_expr}'
    
    return ctx 

def run_func_def (ast_func_def :ast.FunctionDef):
    assert(isinstance(ast_func_def, ast.FunctionDef)) 

    # Find the arguments of the function 
    func_args = ast_func_def.args.args 

    # Initialize the 
    init_ctx = Context() 
    for f_arg in func_args: 
        arg_name = f_arg.arg 
        assert(arg_name not in init_ctx.store) 

        arg_init_val = None 
        init_ctx.store[arg_name] = arg_init_val 

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
            curr_ast_node = curr_ctx.operations[0]
            curr_ctx.operations = curr_ctx.operations[1:]

            if (isinstance(curr_ast_node, ast.Assign)): 
                targets = curr_ast_node.targets 
                assert(isinstance(targets, List))

                expr = curr_ast_node.value 
                val_ctx = run_expr(ast_expr=expr, prev_ctx=curr_ctx)

                assert(len(targets) == len(val_ctx.heap))

                for i, t in enumerate(targets): 
                    val_ctx.store[t.id] = val_ctx.heap[i]

                val_ctx.heap = [] 

                running_contexts.append(val_ctx)

            else: 
                print('[ERROR] unsupported AST node: {}'.format(ast.dump(curr_ast_node)))
                print(f'[ERROR] Context: {curr_ctx}')
                assert(False), f'[ERROR] unsupported AST node: {curr_ast_node}'
