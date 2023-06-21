import networkx as nx
from modules.preprocess import Preprocess
from modules.preprocess_single import PreprocessSingleFunc
import os
from rich.progress import track
from icecream import ic
from multiprocessing import Pool
from multiprocessing import cpu_count
from datetime import datetime
from modules.spec_violation_checker import FuncPairViolationChecker
from modules.ASG_generator import ASGGenerator
from config import cp,DETECT_DATA_ROOT,REPORT_RANKD_SCRIPT,CPU_COUNT,BUG_REPORT_FILE


def time_format():
    return f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}|>'

ic.configureOutput(prefix=time_format,includeContext=True)



class detectWrapper:
    def __init__(self, spec,repo_name='',version=''):
        self.repo_name = spec['repo_name']
        self.version = version
        self.spec = spec
        self.ASG_generator = ASGGenerator(spec)
        self.REPO_DATA_ROOT = os.path.join(DETECT_DATA_ROOT,self.repo_name)
        
                                               

    def detect_bug_for_one_spec(self,work_dir=None): 
        if not os.path.exists(self.REPO_DATA_ROOT):
            os.mkdir(self.REPO_DATA_ROOT)
        
        self.__preprocess()

        if work_dir is None:
            work_dir = f'{self.REPO_DATA_ROOT}/{self.spec["target_API"]}'
        dot_files = os.listdir(f'{work_dir}/cfg-outdir')
        dot_files = [x for x in dot_files if x.endswith('.dot')]
        funcs = open(f'{work_dir}/caller_of_{self.spec["target_API"]}.txt','r').read().split('\n')
        
        p = Pool(processes=CPU_COUNT)
        for dot_file in dot_files:
        # for dot_file in track(dot_files):
            if dot_file.split(".")[0] not in funcs:
                continue
            print(f"[Bug checking] checking usage of target API {self.spec['target_API']} in function",dot_file.split(".")[0])
            p.apply_async(self.detect_bug_in_one_func,(dot_file.split(".")[0],))
        p.close()
        p.join()
        
        
        print(f"Detect completed, check bug reports in file {BUG_REPORT_FILE}")
        # self.__postprocess()
        
        
    def detect_bug_in_one_func(self, test_func) -> bool:
        try:
            critical_var,varScope,func_def = self.ASG_generator.analyze_cfg_for_one_func(test_func)
            self.specChecker = FuncPairViolationChecker(self.spec, critical_var, varScope,func_def)
            return self.specChecker.check_post_operation_for_func(test_func, critical_var)
        except Exception as e:
            print(e)
            
        
    def __preprocess(self):
        # if (not os.path.exists(f'{self.REPO_DATA_ROOT}/{self.spec["target_API"]}')) or (not os.listdir(f'{self.REPO_DATA_ROOT}/{self.spec["target_API"]}/def')):
        Preprocess(self.repo_name,self.spec['target_API'])
    
    
    def __postprocess(self):
        # bug report score
        # bug_report_file = f"{self.REPO_DATA_ROOT}/{REPORT_FILE_NAME}"
        os.system(f'python {BUG_REPORT_FILE} --file {bug_report_file}')



    
    def preprocess_one(self,test_func):
        target_API = self.spec['target_API']
        # if os.path.exists(f'{self.REPO_DATA_ROOT}/{self.spec["target_API"]}/generated_asg/{test_func}-{target_API}.dot'):
        #     return
        # ic("preprocess_one",test_func)
        PreprocessSingleFunc(self.repo_name, self.spec['target_API'],test_func)
