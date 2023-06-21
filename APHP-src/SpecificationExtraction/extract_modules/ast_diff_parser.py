import subprocess
from pydriller import *
import logging
from icecream  import ic
import json
import re  
from extract_modules.patch_simple_parser import PatchSimpleParser
from extract_modules.gumtree_runner import GumTreeRunner
import tree_sitter_helper


from config import cp
from config import DIFF_LEFT_DIR,DIFF_RIGHT_DIR,DIFF_OUT_DIR


logger = logging.getLogger(__name__)



regx = r'\[(\d+),(\d+)\]'

NOT_FUNC = ['unlikely','WARN_ONCE','deb_info','ERR_PTR','PTR_ERR','DEBUGP','IS_ERR','pr_err','ARRAY_SIZE','WARN_ON']

def remove_not_func(func):
    return func not in NOT_FUNC
        
def remove_not_func_from_calls(call):
    return all(func not in call for func in NOT_FUNC)
      
def get_file(path,sha256):
    cmd = f"fdfind {sha256} {path} --no-ignore"
    result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    return result.stdout.read().decode().split('\n')[0]
    
def get_idx_from_tree_node(node):
    code_range = re.search(regx, node)[0]
    left = int(code_range.split(',')[0][1:])
    right = int(code_range.split(',')[1][:-1])
    return left, right
    
    

class ASTDiffParser:
    def __init__(self,repo,hexsha) -> None:
        self.hexsha = hexsha
        self.repo = repo
        self.patch_parser = PatchSimpleParser(self.repo,self.hexsha)
        
        self.inserted_funcs = []
        self.inserted_checks = []

    @classmethod
    def get_inserted_action(cls, diff, code):
        '''
        when insert node is false, we get update node.
        '''
        insert_nodes = list(filter(lambda x: x['action'] == 'insert-node' and not x['tree'].startswith('comment:'), diff))

        insert_tree = list(filter(lambda x: x['action'] == 'insert-tree', diff))
        # ic(insert_nodes, insert_tree)
        return insert_nodes + insert_tree
    
    @classmethod
    def get_updated_action(cls, diff, code):
        return list(filter(lambda x: x['action'] == 'update-node', diff))
    
    @classmethod
    def get_inserted_funcs_call_code(cls, diff,code):
        adds_node = cls.get_inserted_action(diff,code)
        return cls.get_call_exp_code(adds_node,code)

    @classmethod
    def get_inserted_goto(cls, diff,code):
        adds_node = cls.get_inserted_action(diff,code)
        return cls.get_goto_exp(adds_node,code)

    @classmethod
    def get_inserted_funcs_and_checks(cls, diff,code):
        adds_node = cls.get_inserted_action(diff,code)
        func_calls = cls.get_call_exp_code(adds_node,code)
        if func_calls == []:
            updates_node = cls.get_updated_action(diff,code)
            func_calls = cls.get_call_exp_code(updates_node,code)
        
        checks = cls.get_check_exp(adds_node,code)

        # get statement from goto 
        checks_goto, funcs_goto = cls.get_checks_funcs_from_goto(diff,code)
        func_calls+=funcs_goto
        checks+=checks_goto
        func_calls = [func[2] for func in func_calls]
        #unique
        checks = list(set(checks))
        func_calls = list(set(func_calls))

        func_calls = list(filter(remove_not_func_from_calls,func_calls))

        
        return func_calls,checks


    @classmethod
    def print_node(cls, nodes, code):
        for node in nodes:
            left, right = get_idx_from_tree_node(node['tree'])
            # type = node["tree"].split(' ')[0]
            code_slice = code[left:right]
            continue

    @classmethod
    def get_call_exp_code(cls,nodes,code):
        funcs = []
        for node in nodes:
            left,right = get_idx_from_tree_node(node['tree'])
            right = cls.get_nearest_newline(code,right)
            left = cls.get_before_newline(code,left)
            
            code_slice = code[left:right]
            for i in code_slice.split('\n'):
                func,args,call_code = tree_sitter_helper.get_func_name_and_args(i.strip())
                if func:
                    funcs.append((func, args, call_code))
        return funcs

    @classmethod
    def get_nearest_newline(cls,code,idx):
        return next((i for i in range(idx, len(code)) if code[i] == '\n'), 0)

    @classmethod
    def get_before_newline(cls,code,idx):
        try:
            return next((i for i in range(idx, 0,-1) if code[i] == '\n'), 0)
        except Exception:
            return idx
    
    @classmethod
    def get_goto_exp(cls, nodes,code):
        gotos = []
        for node in nodes:
            left,right = get_idx_from_tree_node(node['tree'])
            code_slice = code[left:right]
            goto = tree_sitter_helper.get_goto_label(code_slice)
            if len(goto)!=0:
                gotos += goto
        gotos = list(set(gotos))
        return gotos

    @classmethod
    def unwrap_goto_statment(cls, code,labels):
        return [tree_sitter_helper.get_goto_stat_by_label(code,label) for label in labels]


    @classmethod
    def get_call_exp(cls, nodes,code):
        funcs = []
        for node in nodes:
            left,right = get_idx_from_tree_node(node['tree'])
            code_slice = code[left:right]
            call = tree_sitter_helper.get_func_call(code_slice)
            if len(call)!=0:
                funcs += call
        funcs = list(set(funcs))
        return list(filter(remove_not_func,funcs))
    
    @classmethod
    def get_check_exp(cls, nodes,code):
        checks = []
        for node in nodes:
            left,right = get_idx_from_tree_node(node['tree'])
            code_slice = code[left:right]
            check =  tree_sitter_helper.get_check_expr(code_slice)
            if len(check)!=0:
                checks += check
        
        
        return checks
    
    @classmethod
    def get_inserted_func_call_ASTdiff(cls,repo,sha256):
        GumTreeRunner.run_gumtree_on_commit(repo,sha256)
        diff_file = get_file(DIFF_OUT_DIR,sha256)
        if len(diff_file) == 0:
            ic("fails to run gumtree on ",sha256)
            return []
        code = open(get_file(DIFF_RIGHT_DIR,sha256)).read()
        diff = json.loads(open(diff_file).read())['actions']
        inserted_func_calls = cls.get_inserted_funcs_call_code(diff,code)
        # filter out the func in NOT_FUNC
        checks_goto, funcs_goto = cls.get_checks_funcs_from_goto(diff,code)
        inserted_func_calls+=funcs_goto

        return list(filter(lambda item: item[0] not in NOT_FUNC, inserted_func_calls))
    
    @classmethod
    def get_checks_funcs_from_goto(cls,diff,code):
        # get inserted goto label
        labels = cls.get_inserted_goto(diff,code)
        # get statement in the goto label
        stats =  cls.unwrap_goto_statment(code,labels)
        funcs = []
        checks = []
        # parse these statements, checks, funcs
        for stat in stats:
            check =  tree_sitter_helper.get_check_expr(stat)
            if len(check)!=0:
                checks += check
            func,args,call_code = tree_sitter_helper.get_func_name_and_args(stat)
            if func:
                funcs.append((func, args, call_code))
        return checks,funcs


    def AST_diff_basic(self, repo,hexsha):
        code, diff = self.get_code_diff(repo,hexsha)
        return self.get_inserted_funcs_and_checks(diff,code)
    
    
    def get_code_diff(self,repo,hexsha):
        self.repo = repo
        self.hexsha = hexsha
        repo_name = repo.project_name
        # self.run_gumtree_on_commit(repo,hexsha)
        GumTreeRunner.run_gumtree_on_commit(repo,hexsha,self.patch_parser)
        diff_file = get_file(DIFF_OUT_DIR,hexsha)
        if len(diff_file) == 0:
            return [],[]
        code = open(get_file(DIFF_RIGHT_DIR,hexsha)).read()
        diff = json.loads(open(diff_file).read())['actions']
        return code,diff
