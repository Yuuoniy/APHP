import re
import networkx as nx
import shutil
import os
from rich.progress import track
from icecream import ic
from multiprocessing import Pool
import sys
sys.path.append('../utils')
import tree_sitter_helper
from code_preprocess import CodePreProcessor
from config import cp
from config import DETECT_DATA_ROOT,DETECT_WORK_ROOT,CPU_COUNT


class Preprocess:
    def __init__(self,repo_name,target_API):
        self.repo_name = repo_name
        self.source_dir = cp.get('URL',repo_name)
        self.target_API = target_API
        self.REPO_DATA_ROOT = os.path.join(DETECT_DATA_ROOT,self.repo_name)
        self.DETECT_WORK_ROOT = DETECT_WORK_ROOT
        self.Preprocess_main()

    def Preprocess_main(self):
        
        self.__mkdir_for_data()
        self.__get_caller_of_target_API()
        
        if not os.listdir(f'{self.REPO_DATA_ROOT}/{self.target_API}/def'):
            return
        
        self.__export_CFG_of_callers()
        

    def __mkdir_for_data(self):
        if os.path.exists(f'{self.REPO_DATA_ROOT}/{self.target_API}'):
            return
            # shutil.rmtree(f"{self.DATA_ROOT}/{self.target_API}", ignore_errors=True)
        os.mkdir(f'{self.REPO_DATA_ROOT}/{self.target_API}')
        os.mkdir(f'{self.REPO_DATA_ROOT}/{self.target_API}/def')
        os.mkdir(f'{self.REPO_DATA_ROOT}/{self.target_API}/cfg-outdir')
        # os.mkdir(f'{self.REPO_DATA_ROOT}/{self.target_API}/pdg-outdir')
        os.mkdir(f'{self.REPO_DATA_ROOT}/{self.target_API}/generated_asg')
    
    
    

    def __get_caller_of_target_API(self):
        cmd = f"weggli '{self.target_API}();' {self.source_dir} -A 500 -B 500 -l > {self.REPO_DATA_ROOT}/{self.target_API}/{self.target_API}_callsite"
        # ic(cmd)
        os.system(cmd)
        
        self.get_code_for_each_caller(f'{self.REPO_DATA_ROOT}/{self.target_API}/{self.target_API}_callsite')
        


    def get_code_for_each_caller(self,file):
        data = open(file).read()
        pattern = rf"{self.source_dir}.*\n"
        res = re.split(pattern,data)
        callers_of_target_API = []
        
        for func in res:
            if len(func) == 0:
                continue
            func = CodePreProcessor.clean_code(func)
            funcname = tree_sitter_helper.get_func_name_from_def(func)
            if funcname=='':
                continue
            callers_of_target_API.append(funcname)
            open(f'{self.REPO_DATA_ROOT}/{self.target_API}/def/{funcname}.c','w+').write(func)

        # dump list
        print(f"The number of callers of {self.target_API} is {len(callers_of_target_API)}")
        # ic(len(callers_of_target_API))
        with open(f'{self.REPO_DATA_ROOT}/{self.target_API}/caller_of_{self.target_API}.txt','w+') as f:
            for func in callers_of_target_API:
                f.write(f'{func}\n')


    def __export_CFG_of_callers(self):
        cmd1 = f'joern-parse  {self.REPO_DATA_ROOT}/{self.target_API}/def -o {self.REPO_DATA_ROOT}/{self.target_API}/cpg.bin > /dev/null 2>&1'
        os.system(cmd1)
        
        if os.path.exists(f"{self.REPO_DATA_ROOT}/{self.target_API}/cfg-outdir"):
            shutil.rmtree(f"{self.REPO_DATA_ROOT}/{self.target_API}/cfg-outdir", ignore_errors=True)
            
        cmd1 = f'joern-export  --repr cfg {self.REPO_DATA_ROOT}/{self.target_API}/cpg.bin --out {self.REPO_DATA_ROOT}/{self.target_API}/cfg-outdir > /dev/null 2>&1'
        os.system(cmd1)

        self.__process_CFG_file()




    def __process_CFG_file(self,type='cfg'):
        dot_files = os.listdir(f'{self.REPO_DATA_ROOT}/{self.target_API}/{type}-outdir')
        dot_files = [x for x in dot_files if x.endswith('.dot')]
        funcs = open(f'{self.REPO_DATA_ROOT}/{self.target_API}/caller_of_{self.target_API}.txt','r').read().split('\n')
        os.chdir(f'{self.REPO_DATA_ROOT}/{self.target_API}/{type}-outdir')
        p = Pool(processes=CPU_COUNT)
        for dot_file in dot_files:
            p.apply_async(self.process_CFG_file_one,(dot_file,funcs,type))
        p.close()
        p.join()
        os.chdir(f'{self.DETECT_WORK_ROOT}')
        
        
    def process_CFG_file_one(self, dot_file, funcs, type):
        try:
            G = nx.drawing.nx_agraph.read_dot(f'{self.REPO_DATA_ROOT}/{self.target_API}/{type}-outdir/{dot_file}')

            if G.name not in funcs:
                os.system(f"rm {dot_file}")
            else:
                os.system(f"mv {dot_file} {G.name}.dot")
        except Exception as e:
            print(e)
            
            
