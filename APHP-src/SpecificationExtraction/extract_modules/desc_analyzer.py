# -*- coding:utf-8 -*-
import nltk
from icecream import ic
from pydriller import *

from extract_modules.NLP_utils import *
from extract_modules.patch_simple_parser import PatchSimpleParser
from extract_modules.desc_condition_clause_extractor import ConditionExtractorForText
from extract_modules.diff_parser import DiffParser

import tree_sitter_helper
import spacy

nlp = spacy.load("en_core_web_sm")


commit_func = []


# domain knowlege for commit message
CALL_VERBS = ['increase','free','release','call','decrease','unlock']
CHECK_VERBS = ['check']
CALL_IMPACT = ['leak']





class DescAnalyzer:
    def __init__(self,repo,hexsha):
        self.repo = repo
        self.hexsha = hexsha
        self.key_apis_in_desc = []
        self.modified_func_name = ''
        
        self.patch_parser = PatchSimpleParser(self.repo,self.hexsha)
        # self.patch_parser.get_description()
        
        self.callee_in_func = tree_sitter_helper.get_func_call(self.patch_parser.source_code_after)
        # semantics info mentioned
        self.mentioned_apis = []
        
        # feature 
        self.verbs = []
        self.conds = []

        # post process to get futher info
        self.funcs_in_conds = [item[1] for item in self.conds]
        
        # different ways to get action type: verbs, sec_impact, verbs+sec_impact
        self.action_type_sec_impact = ''
        self.action_type_verbs = ''
        # maybe we need to merge different ways to get action type
        
        
    
    def get_verbs_text(self):
        tokenized = nltk.word_tokenize(self.patch_parser.clean_message)
        self.verbs = [word for (word, pos) in nltk.pos_tag(tokenized) if(pos[:2] == 'VB')]
    
    def get_condition_clause(self):
        condExtractor = ConditionExtractorForText(self.patch_parser.clean_message)
        self.conds = condExtractor.get_condition_in_msg()
        
        clause_sites = self.filter_conds_clause(self.conds)
        ic(self.patch_parser.clean_message,clause_sites)
        
        if (len(clause_sites)==0):
            self.conds =  []
        self.conds = clause_sites
        
    
    
    def remove_subordinate_clause(self,text):
        text = text.lower()
        text = text.replace("()", "")
        doc = nlp(text)

        new_doc = ""
        subordinate_clause = False
        for token in doc:
            if subordinate_clause:
                if token.text in [",", ";", ".", ":", "?", "!"]:
                    subordinate_clause = False
                continue
            if token.text in ["if", "when","before"] or (token.text == "in" and token.nbor(1).text == "case") or (token.text == "in" and token.nbor(1).text == "the" and token.nbor(2).text == "case"):
                subordinate_clause = True
                continue

            new_doc += token.text_with_ws
            
        return new_doc.strip() 
    
    
    # clause need to include a callsite to denote the path.
    def filter_conds_clause(self,subtexts):
        '''
        return mapping list (clause, func)
        '''
        ic(self.hexsha,subtexts)
        #funcs.extend(['error','fail','success']) # why?
        res = []
        if not subtexts:
            return res
        for sub in subtexts:
            res.extend([sub,func] for func in self.callee_in_func if func in sub)
        return res
    
    
    def get_mentioned_API_in_desc(self):
        # prepare
        self.patch_parser.get_modified_func_code()
        
        description = self.patch_parser.get_description()
        description = self.remove_subordinate_clause(description)
        
        modified_func = self.patch_parser.get_modified_func_of_commit()
        if(len(modified_func)) == 0:
            return [],[]
        # get all involved api in description
        self.mentioned_apis = self.funcs_in_desc(description)
        
        self.key_apis_in_desc = list(filter(lambda x: x not in modified_func, self.mentioned_apis))

        return self.key_apis_in_desc, self.mentioned_apis


    def funcs_in_desc(self,description):
        global commit_func
        # ic(description)

        description = text_preprocessor(description)
        token = nltk.word_tokenize(description)
        apis = [k for k in token if len(nltk.corpus.wordnet.synsets(k)) == 0]
        # keep order

        # alias apis pair
        if 'for_each_child_of_node' in apis:
            apis.append('for_each_available_child_of_node')
        if 'for_each_available_child_of_node' in apis:
            apis.append('for_each_child_of_node')

        apis = self.filter_func(sorted(set(apis), key=apis.index))  # unique
        commit_func.extend(apis)
        commit_func = list(set(commit_func))
        return apis


    def get_APH_type_with_sec_impact(self):
        for impact in CALL_IMPACT:
            if impact in self.patch_parser.clean_message:
                ic()
                self.action_type_sec_impact = 'call'
                return self.action_type_sec_impact
    
    def get_action_type_with_verbs(self):
        if self.is_call_type(self.verbs):
            self.action_type_verbs = 'call'
        elif self.is_check_type(self.verbs):
            self.action_type_verbs = 'check'
        return self.action_type_verbs
    
    
    def is_call_type(self,verbs):
        return any(verb in CALL_VERBS for verb in verbs)

    def is_check_type(self,verbs):
        return any(verb in CHECK_VERBS for verb in verbs)

    
    def filter_func(self,apis):
        return list(filter(lambda x: self.is_callee_func(x), apis))


    def is_callee_func(self,func):
        return func in self.callee_in_func

