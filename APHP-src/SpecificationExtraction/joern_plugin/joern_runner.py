from icecream import ic
import os
from joern_plugin.joern_analyzer import JoernDataAnalyzer
from config import JOERN_JSON_DATA, JOERN_BIN_DATA,DIFF_RIGHT_DIR



if not os.path.exists(JOERN_JSON_DATA):
    os.makedirs(JOERN_JSON_DATA)
    
if not os.path.exists(JOERN_BIN_DATA):
    os.makedirs(JOERN_BIN_DATA)
    
class JoernRunner:
    '''
    wrapper for joern
    '''
    def __init__(self) -> None:
        pass
    
    @classmethod
    def dump_dep_info_setup(cls, hexsha, bin_file,func, code):
        bin_file = os.path.join(JOERN_BIN_DATA, bin_file)
        code = f'\"{code}\"'
        json_out = f"{JOERN_JSON_DATA}/{hexsha}_func_call.json"
        JoernDataAnalyzer.get_dependency_info(bin_file,func,code,json_out)
        # read function from file
        try:

            funcs = open(json_out,'r').read().splitlines()
        except Exception as e:
            # ic(f"read function from file {json_out}", e)
            return []
        return funcs
        
    
    @classmethod
    def joern_parse_setup(cls, hexsha, func):
        # ic(hexsha,func)
        if (len(func)==0):
            return ''
        input_file = os.path.join(DIFF_RIGHT_DIR, f'{hexsha}_{func}_code.c')
        bin_file_sub = f"{hexsha}_{func}.bin"
        
        out_file = os.path.join(JOERN_BIN_DATA,bin_file_sub)
        if os.path.exists(out_file):
            return out_file
        JoernDataAnalyzer.joern_parse_to_get_cpg(input_file, out_file)
        return out_file






