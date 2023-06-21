import os
import shutil
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
        
class PreprocessSingleFunc():
    # REPO_DATA_ROOT = DETECT_DATA_ROOT
    WORK_ROOT = DETECT_WORK_ROOT
    def __init__(self, repo_name, target_API,test_func):
        self.source_dir = cp.get('URL',repo_name)
        self.test_func = test_func
        self.target_API = target_API
        self.REPO_DATA_ROOT = os.path.join(DETECT_DATA_ROOT,repo_name)
        if not os.path.exists(self.REPO_DATA_ROOT):
            os.mkdir(self.REPO_DATA_ROOT)
        self.Preprocess_main()
        
        
    def Preprocess_main(self):
        
        self.get_caller_of_context()
        self.call_joern()
        self.process_dot_files()
    
    def get_caller_of_context(self):
        # func = 'of_parse_phandle'
        if os.path.exists(f'{self.REPO_DATA_ROOT}/{self.target_API}'):
            # return
            shutil.rmtree(f"{self.REPO_DATA_ROOT}/{self.target_API}", ignore_errors=True)
            
        os.mkdir(f'{self.REPO_DATA_ROOT}/{self.target_API}')
        os.mkdir(f'{self.REPO_DATA_ROOT}/{self.target_API}/def')
        os.mkdir(f'{self.REPO_DATA_ROOT}/{self.target_API}/cfg-outdir')
        os.mkdir(f'{self.REPO_DATA_ROOT}/{self.target_API}/generated_asg')
        cmd = f"weggli '{self.target_API}();' {self.source_dir} -A 500 -B 500 -l > {self.REPO_DATA_ROOT}/{self.target_API}/{self.target_API}_callsite"
        # ic(cmd)
        os.system(cmd)
        self.split_data(f'{self.REPO_DATA_ROOT}/{self.target_API}/{self.target_API}_callsite')
        
    
    def call_joern(self):
        bin_file = f'{self.REPO_DATA_ROOT}/{self.target_API}/{self.test_func}_cpg.bin'
        # if os.path.exists(bin_file):
        #     return
        source = f'{self.REPO_DATA_ROOT}/{self.target_API}/def/{self.test_func}.c'
        parse_cmd = f'joern-parse  {source} -o {bin_file} > /dev/null 2>&1'
        os.system(parse_cmd)

        export_cmd = f'joern-export  --repr cfg {bin_file} --out {self.REPO_DATA_ROOT}/{self.target_API}/cfg-{self.test_func}-outdir > /dev/null 2>&1'
        # ic(export_cmd)
        os.system(export_cmd)
    
    
    def process_dot_files(self,type='cfg'):
        try:
            cfg_dir = f'{self.REPO_DATA_ROOT}/{self.target_API}/cfg-{self.test_func}-outdir'
            dot_files = [x for x in os.listdir(cfg_dir) if x.endswith('.dot')]
            os.chdir(cfg_dir)
            for dot_file in dot_files:
            # for dot_file in track(dot_files):
                self.process_dot_file_one(cfg_dir,dot_file,type)
        
            os.chdir(f'{self.WORK_ROOT}')
        except Exception as e:
            ic(e)
        
    def split_data(self,file):
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
        # ic(len(callers_of_target_API))
        with open(f'{self.REPO_DATA_ROOT}/{self.target_API}/caller_of_{self.target_API}.txt','w+') as f:
            for func in callers_of_target_API:
                f.write(f'{func}\n')
                
    def process_dot_file_one(self, cfg_dir, dot_file, type):
        G = nx.drawing.nx_agraph.read_dot(f'{cfg_dir}/{dot_file}')

        if G.name not in [self.test_func]:
            os.system(f"rm {dot_file}")
        else:
            os.system(f"mv {dot_file} ../cfg-outdir/{G.name}.dot")
    
