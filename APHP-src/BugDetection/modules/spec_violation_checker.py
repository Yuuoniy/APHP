import networkx as nx
import os
import pandas as pd
from icecream import ic
import sys
sys.path.append('../utils')
import cfg_analyzer as cfg_analyzer
import tree_sitter_helper
from typing import List
from modules.report_verifier import ReportVerifier
import traceback
from config import cp, BUG_REPORT_FILE,DETECT_DATA_ROOT
from path_classifier import PathClassifier



class FuncPairViolationChecker:
    methods = []
    funcs_cfg =['(METHOD_RETURN,','(METHOD,' ,'(RETURN,',] 
    critical_variable = ''


    def __init__(self,spec,critical_var='',varScope='',func_def=''):
        self.spec = spec
        self.repo_name = spec['repo_name']
        self.source_dir = cp.get('URL',self.repo_name)
        
        self.target_API = spec['target_API']
        self.post_operation = spec['post_operation'].split("|")
        self.critical_var_role = spec['critical_var_role']
        self.pre_condition = spec['pre_condition']
        self.post_condition = spec['post_condition']
        self.critical_variable = critical_var
        self.varScope = varScope
        self.func_def = func_def
        self.REPO_DATA_ROOT = os.path.join(DETECT_DATA_ROOT,self.repo_name)
        
    
    def check(self,test_func)->bool:
        isBuggy = self.check_post_operation_for_func(test_func)
     
    def verifier_report_is_FP(self,func,violated_path_num)->bool:
        # autofree
        if tree_sitter_helper.is_autofree_var(self.func_def,self.critical_variable):
            return True
        try:
            ver = ReportVerifier(self.spec,func,violated_path_num,self.critical_variable)
            return ver.check()
        except Exception as e:
            traceback.print_exc()
            ic(e)
    
    
    def check_if_has_wrapper_post_op(self,violate_paths,dot_file):
        G = nx.drawing.nx_agraph.read_dot(dot_file)
        to_check_funcs = self.get_all_funcs_in_path(G)
        return any(self.func_has_post_op_inside(func[0]) for func in to_check_funcs)
        
    
    def func_has_post_op_inside(self,func) -> bool:
        # post_ops = self.post_operation.split('|')
        for post_operation in self.post_operation:
            query = f"weggli '_ {func}(_){{{post_operation}($ret);}}' {self.source_dir}"
            # ic(query)
            if res := ReportVerifier.run_query(query):
                return True
    
    def get_all_funcs_in_path(self,G):
        funcs = []
        keywords = ['free','clean','remove']
        # iterate all labels in G
        labels = list(nx.get_node_attributes(G, "label").values())
        for label in labels:
            stmt = label.split(',',1)[1][:-1]
            func,args,code = tree_sitter_helper.get_func_name_and_args(stmt)
            if func:
                funcs.append((func, args, code))
        return [func for func in funcs if any(keyword in func[0] for keyword in keywords)]
        

    
    def check_post_operation_for_func(self,test_func,critical_var = '',dot_file=None,write=True):
        dot_file = dot_file if dot_file is not None else self.get_dot_file(test_func)
        if not os.path.exists(dot_file):
            # print(f'file {dot_file} not exist')
            return False
        try:
            violate_paths = self.path_verification(dot_file)

            if self.__check_violate_paths_by_type(violate_paths):
                return self.__check_potential_false_positive(
                    violate_paths, test_func, dot_file, write
                )
            else:
                return False
        except Exception as e:
            print(f"fail to test function {test_func} due to {e}")
            return False


    def __check_potential_false_positive(self, violate_paths, test_func, dot_file, write):
        # futher check
        violated_path_num = violate_paths.count(False)
        if(self.verifier_report_is_FP(test_func,violated_path_num)):
            return False

        # check if perform alternative post_operation
        if(self.check_if_has_wrapper_post_op(violate_paths,dot_file)):
            return False

        if write:
            self.record_buggy_site(test_func,violated_path_num)
        print(f"[bug report] {test_func} may lack post operation {self.post_operation} for {self.target_API}")
        return True


    def path_verification(self,dot_file):
        error_paths,non_error_paths = self.sort_paths(dot_file)
        G = nx.drawing.nx_agraph.read_dot(dot_file)

        tested_paths = self.get_satisfied_paths(G,error_paths,non_error_paths)
        if tested_paths is None or len(tested_paths) == 0:
            return []
        violate_paths = [self.check_operations_in_path(G,path,False) for path in tested_paths]
        return violate_paths


    def __check_violate_paths_by_type(self,violate_paths):
        if self.post_condition == 'error':
            return violate_paths.count(False) > 1
        if self.post_condition == 'all':
            return violate_paths.count(False) >= 1
        
    

    def get_dot_file(self,test_func):
        return f"{self.REPO_DATA_ROOT}/{self.target_API}/generated_asg/{test_func}-{self.target_API}.dot"

    def record_buggy_site(self,test_func,violated_path_num):
        post_ops = "|".join(self.post_operation)
        cols=['repo_name','test_func','target_API','post_operation','critical_var_role','critical_var_name','critical_var_scope','violated_path_num']
        bug_item = pd.DataFrame([[self.repo_name, test_func,self.target_API,post_ops,self.critical_var_role, self.critical_variable, self.varScope,violated_path_num]],columns=cols)
        
        bug_item.to_csv(BUG_REPORT_FILE,mode='a+',index=False,header=not os.path.exists(BUG_REPORT_FILE))


    
    def get_satisfied_paths(self,G,error_paths,non_error_paths):
        if self.post_condition == 'error':
            return error_paths
        return error_paths+non_error_paths

    def check_operations_in_path(self,G,path,is_error=True):
        for node in path:
            # if any(func in labels[node] for func in self.funcs_cfg):
            if any(post_operation in G.nodes[node]['label'] for post_operation in self.post_operation):
                if is_error:  
                    print(cfg_analyzer.format_path(G,path))
                return True
        return False

    def sort_paths(self,dot_file):
        G = nx.drawing.nx_agraph.read_dot(dot_file)
        if G.number_of_nodes() == 0:
            # ic("emprty graph",dot_file)
            return [],[]
        source = list(nx.topological_sort(G))[0]
        target = cfg_analyzer.node_id_by_label(G,'METHOD_RETURN')
        error_paths = []
        non_error_paths = []
        escape_paths = [] # these path return critical variable
        paths = list(nx.all_simple_paths(G, source=source, target=target))
        
        return_nodes_in_paths = [cfg_analyzer.get_return_node(G,path) for path in paths]
        
        # Use the PathClassifier to classify paths
        path_classifier = PathClassifier(G)
        success_vals, error_vals = path_classifier.workflow()

        for path in paths:
            cfg_analyzer.format_path(G, path)
            path_type = PathClassifier.check_is_path_type(G, success_vals, error_vals, path)
            if path_type == 'error':
                error_paths.append(path)
            elif cfg_analyzer.check_is_escaped_path(G, path, self.critical_variable):
                escape_paths.append(path) # to test
            else:
                non_error_paths.append(path)
            
        self.print_path_info(G,error_paths,non_error_paths,escape_paths)

        return error_paths,non_error_paths

    



    def print_path_info(self,G,error_paths,non_error_paths,escape_paths):
        # ic(len(error_paths),len(non_error_paths),len(escape_paths))
        for path in error_paths:
            cfg_analyzer.print_return_node_in_path(G,path)
        for path in escape_paths:
            cfg_analyzer.print_return_node_in_path(G,path)
        for path in non_error_paths:
            cfg_analyzer.print_return_node_in_path(G,path)
            
  
