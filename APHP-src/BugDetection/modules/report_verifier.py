import subprocess
from icecream import ic
import configparser
import os
from config import cp
from config import DETECT_DATA_ROOT
# cp = configparser.RawConfigParser()
# cp.read('/root/bug-tools/config/config.cfg')

class ReportVerifier:
    # verifier to reduce false positives
    def __init__(self,spec,test_func,violated_path_num,critical_variable):
        try:
            self.target_API = spec['target_API']
            self.critical_var_role = spec['critical_var_role']
            self.REPO_DATA_ROOT = os.path.join(DETECT_DATA_ROOT,spec['repo_name'])
            self.code_file = f'{self.REPO_DATA_ROOT}/{self.target_API}/def/{test_func}.c'
            self.post_operation = spec['post_operation']
            self.repo_name = spec['repo_name']
            self.pre_condition = spec['pre_condition']
            self.violated_path_num = violated_path_num
            self.critical_variable = critical_variable
        except Exception as e:
            ic(e)
        
    
    
    def check(self) -> bool:
        if self.critical_var_role == 'retval':
            isFP = False
            if isFP := self.has_var_constraints():
                return isFP
            if isFP := self.has_callback():
                return isFP
            if isFP := (self.has_retval_check() and self.violated_path_num == 1 and self.pre_condition == 'success'):
                return isFP
        return False
    
    def has_retval_check(self) -> bool:
        # if the main api has retval check, violate path num should larger than 1
        query1 = f"weggli '$ret={self.target_API}();if(!$ret)_;' {self.code_file}"
        query2 = f"weggli '$ret={self.target_API}();if($ret==NULL)_;' {self.code_file}"
        query3 = f"weggli '$ret={self.target_API}();if($ret<0)_;' {self.code_file}"
        # query3 = f"weggli '$ret={self.target_API}();if($ret!=NULL)_;' {self.code_file}"
        # ic(query1,query2)
        res1 = self.run_query(query1)
        res2 = self.run_query(query2)
        res3 = self.run_query(query3)
        return len(res1) > 0 or len(res2) > 0 or len(res3) > 0
    
    
    def has_var_constraints(self) -> bool:
        post_ops = self.post_operation.split('|')
        for post_operation in post_ops:
            query1 = f"weggli '$ret={self.target_API}();if($ret)_; {post_operation}($ret);' {self.code_file}"
            query2 = f"weggli '$ret={self.target_API}();if($ret!=-1)_; {post_operation}($ret);' {self.code_file}"
            query3 = f"weggli '$ret={self.target_API}();if($ret!=NULL)_; {post_operation}($ret);' {self.code_file}"
            query4 = f"weggli 'if(_($var)){{ {post_operation}($var);}}' {self.code_file}"
            res1 = self.run_query(query1)
            res2 = self.run_query(query2)
            res3 = self.run_query(query3)
            res4 = self.run_query(query4)
            if(len(res1) > 0 or len(res2) > 0 or len(res3) > 0) or len(res4) > 0:
                return True
        return False
    

    def has_callback(self)->bool:
        query = f"weggli -R 'callback_func=add_action_or_reset$' '{self.target_API}(); $callback_func();' {self.code_file}"
        res = self.run_query(query)
        return len(res) > 0
    
    @classmethod
    def run_query(cls,cmd):
        result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        return result.stdout.read().decode().split('\n')[0]
    
