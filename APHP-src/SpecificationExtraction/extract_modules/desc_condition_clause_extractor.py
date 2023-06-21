#!/root/o/tools/tree-sitter/weggli/.env-weggli/bin/python
# -*- coding:utf-8 -*-
# https://stackoverflow.com/questions/39320015/how-to-split-an-nlp-parse-tree-to-clauses-independent-and-subordinate
import nltk
from stanfordcorenlp import StanfordCoreNLP
from nltk import Tree
from icecream import ic
import pandas as pd
from pandarallel import pandarallel
from functools import reduce
import extract_modules.NLP_utils  as NLP_utils
import operator
from nltk.tokenize import sent_tokenize
from config import CORENLP_PATH

nlp = StanfordCoreNLP(CORENLP_PATH)


class ConditionExtractorForText:
    """
    given text, get condition through dependency analysis
    """
    def __init__(self, text) -> None:
        self.text = text


    def get_condition_in_msg(self):
        return self.get_clause_from_nltk_subtree()

    def get_clause_from_nltk_subtree(self):
        self.text = self.text.replace('(','').replace(')','')
        self.text = self.coreference_resolution(self.text)
        try:
            parse_str = nlp.parse(self.text)
        except Exception as e:
            ic(f"parse error {self.text}", e)
            return []
        t = Tree.fromstring(parse_str)

        subtexts = [' '.join(subtree.leaves()) for subtree in t.subtrees() if subtree.label() in ["SBAR", "PP", "ADJP"]]

        if not subtexts:
            return []
        


    def coreference_resolution(self,text):
        text = text.replace('(','').replace(')','').lower()
        text = NLP_utils.process_abbreviation(text)
        tokens = [nltk.word_tokenize(sent) for  sent in sent_tokenize(text)]
        corefs = nlp.coref(text)
        try:
            for coref_relation  in corefs:
                first_word = coref_relation[0][3]
                for mention in coref_relation[1:]:
                    # replace words
                    tokens[mention[0]-1][mention[1]-1:mention[2]-1] = [first_word]
        except Exception:
            print("Error")

        tokens = reduce(operator.concat,tokens,[])
        return ' '.join(tokens)

