from gc import collect
from logging import critical
import os
import traceback
import pandas as pd
import nltk
from icecream import ic
import sys
from icecream import ic
sys.path.append('/root/APHP/APHP-src')

from utils import tree_sitter_helper
from extract_modules.collect_path_condition import pathCondCollector
from extract_modules.patch_simple_parser import PatchSimpleParser
from extract_modules.desc_analyzer import DescAnalyzer
from extract_modules.ast_diff_parser import ASTDiffParser
from extract_modules.diff_parser import DiffParser

from extract_modules.API_pair_checker import APIPairChecker
from joern_plugin.joern_runner import JoernRunner



from pydriller import Git
import configparser
from config import cp



ic.configureOutput(includeContext=True)



NOT_FUNC = ['unlikely','WARN_ONCE','deb_info','ERR_PTR','PTR_ERR','DEBUGP','IS_ERR','ERR_CAST','memcpy']




class SpecExtractor:
    def __init__(self,repo,hexsha):
        
        # basic info
        self.repo = repo
        self.hexsha = hexsha
        
        # key elements in APH specification
        self.op_type = ''
        self.critical_var = ''
        self.critical_var_role = ''
        self.target_API = ''
        self.post_cond = 'error' # default conditions
        self.pre_cond = 'success' # default conditions
        self.post_operation = '' # entire code
        self.post_op_name = '' # function name of post_operation
        
        
        # for intermediate output
        self.call_dep_on_post_op = []
        self.key_apis_in_msg = []
        self.target_API_candidates = []
        self.post_op_cands = []

        self.action_type_verbs = [] # infer patch type through verb
        self.funcs_in_conds = []
        self.call_func_map = []

        self.isInferred = False
        # output of diff analysis
        self.inserted_funcs_call = []
        self.inserted_checks = []

        # output of joern analysis
        self.bin_file = ''

        # patch overview
        self.modified_func_name = ''
        self.modified_func_code = ''
        self.msg = ''

        # status flag for information extraction
        self.is_post_op_found = False
        self.is_target_API_found = False
        self.is_critical_var_found = False
        self.is_call_dep_found = False
        self.is_key_apis_found = False
        self.is_target_API_cand_found = False
        self.is_type_in_verbs_found = False
        self.is_funcs_in_conds_found = False
        self.state = 'init'
        self.explore_path = ''


        # some intermediate output
        self.func_in_msg_and_inserted = []
        self.func_in_msg_and_callee = []
        self.target_API_callsite = []
        
        # subclass, use them to access more specific information
        self.patch_parser = PatchSimpleParser(self.repo,self.hexsha)
        self.desc_analyzer = DescAnalyzer(self.repo,self.hexsha)
        self.joern_runner = JoernRunner()
        self.ast_diff_parser = ASTDiffParser(self.repo,self.hexsha)
        self.diff_parser = DiffParser(self.repo,self.hexsha)
        
        # action type from different source 
        self.action_type_raw_diff = ''
        self.action_type_sec_imp = ''
        self.action_type_verbs = ''
        
        

    def extract_spec_from_patch_one(self):
        # Preprocess
        self.__preprocess()

        # APH specification identification
        self.__identify_post_operation()
        self.__get_target_API_candidates()
        self.__identify_target_API()
        self.__identify_critical_var_role_in_target_API()
        self.__collect_path_post_cond()
        

        specification = [self.hexsha,self.target_API,self.post_op_name,self.op_type,self.critical_var_role,self.pre_cond,self.post_cond]
        
        spec_dict = {'target_API':self.target_API,'post_operation':self.post_op_name,'critical variable':self.critical_var_role,'self.pre_condition':self.pre_cond,'post_condition':self.post_cond}
        print(f"extract specification from patch {self.hexsha} : {spec_dict}")
        return specification



    def __preprocess(self):
        self.__pre_analysis_desc()
        self.__pre_analysis_code()
        self.__pre_analysis_diff()
        self.__parse_entity()


    def __pre_analysis_desc(self):
        # nlp analysis
        self.desc_analyzer.get_verbs_text()
        self.action_type_verbs = self.desc_analyzer.get_action_type_with_verbs()
        self.funcs_in_conds = [item[1] for item in self.desc_analyzer.conds]
        
        apiExtractor = DescAnalyzer(self.repo,self.hexsha)
        
        self.key_apis_in_msg, apis = apiExtractor.get_mentioned_API_in_desc()

        


    def __pre_analysis_code(self):
        # joern analysis
        self.patch_parser.get_modified_func_of_commit()
        self.patch_parser.get_modified_func_code()
        
        try:
            self.modified_func_name = self.patch_parser.modified_func_name
            self.modified_func_code = self.patch_parser.source_code_after
            # ic(self.modified_func_name)
            self.bin_file = self.patch_parser.get_bin_file()
            # ic()
        except Exception as e:
            ic(self.modified_func_name)
            ic(e)


    def __pre_analysis_diff(self):
        astParser = ASTDiffParser(self.repo,self.hexsha)
        inserted_funcs_call_ast_diff, self.inserted_checks = astParser.AST_diff_basic(self.repo, self.hexsha)
        # ic(inserted_funcs_call_ast_diff, self.inserted_checks)

        inserted_call_origin_diff = self.diff_parser.get_inserted_func_calls()
        inserted_call_origin_diff_new = []

        # heuerist way, only use put.
        if (len(inserted_funcs_call_ast_diff)>1):
            for call in inserted_funcs_call_ast_diff:
                if "of_node_put" in call:
                    inserted_call_origin_diff_new.append(call)
                inserted_call_origin_diff = inserted_call_origin_diff_new


        # get inserted func both in original diff and AST diff
        self.inserted_funcs_call = [item[2] for item in inserted_call_origin_diff if item[2] in inserted_funcs_call_ast_diff] or inserted_funcs_call_ast_diff or [item[2] for item in inserted_call_origin_diff] 


    def __parse_entity(self):
        self.inserted_funcs_name = [tree_sitter_helper.get_func_name_and_args(call)[0] for call in self.inserted_funcs_call]
        identifiers = [tree_sitter_helper.get_idents_in_expr(call) for call in self.inserted_funcs_call]
        identifiers += [tree_sitter_helper.get_idents_in_expr(check) for check in self.inserted_checks]
        self.call_func_map = dict(zip(self.inserted_funcs_name,self.inserted_funcs_call))
        self.stat_var_map = dict(zip(self.inserted_funcs_call+self.inserted_checks,identifiers))



    def __get_target_API_candidates(self):
        if self.post_operation in ['', 'unknown']:
            return
        # get dependency call of post_operation
        self.call_dep_on_post_op = JoernRunner.dump_dep_info_setup(self.hexsha,self.bin_file,self.post_op_name,self.post_operation)
        
        self.target_API_candidates = list(set(self.key_apis_in_msg)&(set(self.call_dep_on_post_op))) # seems not need to...
        self.target_API_candidates = list(filter(lambda item: item not in NOT_FUNC, self.target_API_candidates))
        


    def get_post_op_call_with_func_in_desc_and_inserted(self):
        self.post_op_cands = self.func_in_msg_and_inserted
        if len(self.func_in_msg_and_inserted) > 1:
            self.filter_post_op_with_cond_clause()
        self.post_operation = self.call_func_map[self.post_op_cands[0]]
        self.post_op_name = self.post_op_cands[0]
        self.get_critical_var()
        self.op_type = 'call'


    def filter_post_op_with_cond_clause(self):
        # filter out post_op_cands that not in condition
        # idea: in condition is not the action
        self.post_op_cands = [item for item in self.post_op_cands if item not in self.funcs_in_conds]

    def __identify_post_operation(self):
        # get security operation from diff
        # ic(self.inserted_funcs_call,self.inserted_funcs_name)
        inter_set = set(self.key_apis_in_msg) & set(self.inserted_funcs_name)
        self.func_in_msg_and_inserted = list(inter_set)
        # pdb.set_trace()
        if self.func_in_msg_and_inserted: # condition one , msg has security operation
            self.get_post_op_call_with_func_in_desc_and_inserted()
        elif self.inserted_funcs_name and (self.action_type_verbs == 'call' or self.op_type == 'call'):  # condition two, msg has no security operation, but has call
            self.post_operation = self.call_func_map[self.inserted_funcs_name[0]]
            self.post_op_name = self.inserted_funcs_name[0]
            self.op_type = 'call'
            self.get_critical_var()
        elif self.inserted_checks:
            self.post_operation = self.inserted_checks[0]
            self.get_critical_var()
            self.op_type = 'check'
        elif self.inserted_funcs_name: # condition three, msg has no info, get only from code
            # ic(self.inserted_funcs_name[0])
            self.post_operation = self.call_func_map[self.inserted_funcs_name[0]]
            self.post_op_name = self.inserted_funcs_name[0]
            self.op_type = 'call'
            self.get_critical_var()
        elif self.action_type_raw_diff == 'check':
            check_stat = self.diff_parser.get_inserted_checks()
            self.post_operation = check_stat
            self.op_type = 'check'
        elif self.action_type_raw_diff == 'call':
            # func_call = analysis_diff.get_inserted_func_call_from_commit(self.repo,self.hexsha)[0]
            func_call = self.diff_parser.get_inserted_func_calls()

            self.post_operation = func_call[2]
            self.critical_var = func_call[1]
            self.op_type = 'call'
        else:
            self.post_operation = 'unknown'
            self.op_type = 'unknown'
            self.critical_var = 'unknown'



    def get_critical_var(self):
        self.critical_var = self.stat_var_map[self.post_operation]


    def __identify_target_API(self):
        api_pair_checker = APIPairChecker() 
        
        

        # ic(self.key_apis_in_msg,self.call_dep_on_post_op,self.target_API_candidates)
        if len(self.target_API_candidates) == 1:
            self.isInferred = True
            self.target_API = self.target_API_candidates[0]
        else:
            self.identify_target_API_by_return_value(check_if_in_cand=True)
            if self.target_API != 'unknown':
                return
        
        if len(self.target_API_candidates) > 1:
            self.isInferred = True
            self.target_API = api_pair_checker.find_api_pair(self.post_op_name,self.target_API_candidates)

            
        elif not self.target_API_candidates:
            self.target_API_candidates = self.call_dep_on_post_op
            self.identify_target_API_by_return_value(check_if_in_cand=True)
            if self.target_API != 'unknown':
                return
            if len(self.target_API_candidates) > 1:
                self.isInferred = True
                self.target_API = api_pair_checker.find_api_pair(self.post_op_name,self.target_API_candidates)
            if self.target_API == 'unknown':
                self.identify_target_API_by_return_value(check_if_in_cand=False)

    
    def identify_target_API_by_return_value(self,check_if_in_cand=True):
        try:
            if retval_func_call := tree_sitter_helper.get_return_value_assign_func_call(self.modified_func_code, self.critical_var[0]):
                if (
                    check_if_in_cand
                    and retval_func_call in self.target_API_candidates
                    or not check_if_in_cand
                ):
                    self.target_API = retval_func_call
                else:
                    self.target_API = 'unknown'
            else:
                self.target_API = 'unknown'
        except Exception:
            self.target_API = 'unknown'
            traceback.print_exc()
            
            
            

    def __identify_critical_var_role_in_target_API(self):
        # input: target_callsite, variable name
        # output: role of variable in target_API_callsite
        # is return val or argument val
        self.get_target_API_callsite()
        if len(self.target_API_callsite) == 0 or len(self.critical_var) == 0:
            return
        vals = tree_sitter_helper.get_retval_and_args_in_callsite(self.target_API_callsite[0])
        # ic(vals)
        if self.critical_var[0] == vals['retval'] or self.critical_var[0] in vals['retval']: # struct/field
            self.critical_var_role = 'retval'
        elif self.critical_var[0] in vals['args']:
            index = vals['args'].index(self.critical_var[0])
            self.critical_var_role = f'arg{str(index)}'
    

    def get_target_API_callsite(self):
        self.target_API_callsite = tree_sitter_helper.get_func_callsite_from_code(self.modified_func_code,self.target_API)


    
    def __collect_path_post_cond(self):
        if self.target_API == 'unknown':
            return
        try:
            collector = pathCondCollector(hexsha=self.hexsha, source_code_file=self.patch_parser.source_code_after_path, bin_file=self.patch_parser.bin_file, target_API=self.target_API,post_operation=self.post_operation)
            self.post_cond = collector.collect_conds()
            # ic(self.post_cond)
        except Exception:
            self.post_cond = 'error'
