import sys
import os
import re
from icecream import ic


import tree_sitter_helper

# parser = tree_sitter_helper.tree_sitter_init()
# CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
# DIFF_LEFT_DIR =  "/root/bug-tools/commitAnalyzer/data/before/"
# DIFF_RIGHT_DIR =  "/root/bug-tools/commitAnalyzer/data/after/"
# DIFF_OUT_DIR = "/root/bug-tools/commitAnalyzer/data/diff/"


# INTERMEDIATE_DATA_DIR = os.path.join(CURRENT_DIR, 'intermediate_data')

# if os.path.exists(INTERMEDIATE_DATA_DIR) == False:
#     os.mkdir(INTERMEDIATE_DATA_DIR)


class CodePreProcessor:
    def __init__(self, code):
        self.code = code

    def __str__(self):
        return self.code
    
    
    @classmethod
    def replace_unhealth_code(cls,code):
        code = code.replace("__init",'')
        code = code.replace("__devinit",'')
        code = code.replace("__iomem",'')
        code = re.sub(r"(STACK_OF\()(?P<cont>[^\)]*)(\))", lambda m: 'int', code)
        return code
    
    @classmethod
    def remove_def_code(cls,code):
        code = code.split('\n')
        code = [line for line in code if line.startswith('#ifdef') == False]
        code = [line for line in code if line.startswith('#endif') == False]
        code = [line for line in code if line.startswith('#else') == False]
        return "\n".join(code)
        
    
    @classmethod
    def clean_code(cls, code):
        code = cls.replace_unhealth_code(code)
        code = cls.remove_def_code(code)
        return code
    
    @classmethod
    def get_ident(cls, statement):
        return next((idx for idx, i in enumerate(statement) if not i.isspace()), -1)
    
    
    
    @classmethod
    def dump_func_code(cls, source_code, method, file):
        source_code = source_code.split('\n')
        func_code = '\n'.join(source_code[method.start_line - 1:method.end_line])
        func_code = CodePreProcessor.clean_code(func_code)
        open(file, 'w+').write(str(func_code))
        return func_code
        
        
    @classmethod
    def convert_loop_statement_to_if(cls, code):
        code = code.split('\n')
        unroll_loop_code = []
        for statement in code:
            if 'for' in statement and tree_sitter_helper.parse_for_statement(statement):
                ident = statement[:cls.get_ident(statement)]
                for_statement = tree_sitter_helper.parse_for_statement(statement)
                if_statement = f"{ident}if (" + for_statement['condition'] + ") "
                if statement.endswith('{'):
                    if_statement += "{"
                set_statement = ident + for_statement['initializer'] + ';'
                unroll_loop_code.extend((set_statement, if_statement))
            elif 'while' in statement and tree_sitter_helper.parse_while_statement(statement):
                ident = statement[:cls.get_ident(statement)]
                while_statement = tree_sitter_helper.parse_while_statement(statement)
                if_statement = f"{ident}if " + while_statement['condition']
                if statement.endswith('{'):
                    if_statement += "{"
                unroll_loop_code.append(if_statement)
            else:
                unroll_loop_code.append(statement)
        return '\n'.join(unroll_loop_code)