from pydriller import *
import os
from git import Repo
import configparser
import sys
sys.path.append('../utils')
from code_preprocess import CodePreProcessor
from icecream import ic
from config import cp
from config import DIFF_LEFT_DIR,DIFF_RIGHT_DIR,desc_tags_prefixes

from joern_plugin.joern_runner import JoernRunner




class PatchSimpleParser:
    """a simple parser for patch
       this has basic infos about the patch, like:
       hexsha, message, modified_func_list, modified_func_name, clean_message, source_code_before, source_code_after, source_code_before_path, source_code_after_path, bin_file

    """    
    def __init__(self, repo, hexsha) -> None:
        self.hexsha = hexsha
        self.repo = repo
        self.modified_func_list = []
        self.modified_func_name = ''
        self.clean_message = ''
        self.source_code_before = ''
        self.source_code_after = ''
        self.source_code_before_path = '' # This is source code filepath, not the path in CFG.
        self.source_code_after_path = '' 
        self.bin_file = ''
        self.data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'code_data',self.hexsha)
        self.get_description()
        self.get_modified_func_code()
    
    

    
    def get_description(self):
        commit = self.repo.get_commit(self.hexsha)
        lines = commit.msg.splitlines()
        lines_filter = list(
            filter(lambda x: not x.startswith(tuple(desc_tags_prefixes)), lines))
        message = " ".join(lines_filter[1:])
        self.clean_message = message
        return message

   
    def get_modified_func_of_commit(self):
        commit = self.repo.get_commit(self.hexsha)
        func = []
        try:
            for f in commit.modified_files:
                func.extend(method.name for method in f.changed_methods)
            self.modified_func_name = func[0]
        except Exception as e:
            ic(e, self.hexsha)
            # raise e

        return func 

    
    def get_modified_func_code(self):
        commit = self.repo.get_commit(self.hexsha)
        try:
            for f in commit.modified_files:
                if f.change_type != ModificationType.MODIFY:
                    continue
                for method in f.changed_methods:
                    return self.__get_func_of_two_versions(method, f)
            return '',''
        except Exception as e:
            ic(e)
            return '',''


    def __get_func_of_two_versions(self, method, f):
        method_before = list(filter(lambda x: x.name==method.name, f.methods_before))
        if not method_before:
            return
        method_before = method_before[0]

        self.source_code_after_path = f'{DIFF_RIGHT_DIR}{self.hexsha}_{method.name}_code.c'
        self.source_code_before_path = f'{DIFF_LEFT_DIR}{self.hexsha}_{method.name}_code.c'
        self.source_code_after = CodePreProcessor.dump_func_code(f.source_code,method,self.source_code_after_path)
        self.source_code_before = CodePreProcessor.dump_func_code(f.source_code_before,method_before,self.source_code_before_path)
        return self.source_code_after_path,self.source_code_before_path
    
    
    def get_bin_file(self):
        if len(self.source_code_after_path) == 0:
            self.get_modified_func_code()
        
        self.bin_file = JoernRunner.joern_parse_setup(self.hexsha,self.modified_func_name)
        
        return self.bin_file

    