import re
import nltk
# import spacy
from nltk.tokenize import sent_tokenize
from icecream import ic
import os
import textacy
import string
import json
# import spacy

# nlp = spacy.load("en_core_web_sm")


abbrs = {"don't": "do not", "Don't": "do not", "doesn't": "does not", "Doesn't": "does not",
            "didn't": "did not","wasn't":"was not",
            "couldn't": "could not", "Couldn't": "could not", "can't": "can not", "Can't": "can not",
            "ca n't": "can not", "Ca n't": "can not",
            "shouldn't": "should not", "Shouldn't": "should not", "should've": "should have",
            "mightn't": "might not", "mustn't": "must not", "Mustn't": "must not", "needn't": "need not",
            "haven't": "have not", "hadn't": "had not", "hasn't": "has not",
            "you'd": "you should", "You'd": "you should", "you're": "you are", "You're": "you're",
            "it's": "it is", "It's": "it is", "won't": "will not", "wo n't": "will not",
            "isn't": "is not", "Isn't": "is not", "aren't": "are not", "Aren't": "are not"}


def get_pos_tag():
    text = "I am very happy to be here today"
    tokens = nltk.word_tokenize(text)
    pos_tagged_tokens = nltk.pos_tag(tokens)


def writeFile(listdata, filepath):
    f = open(filepath, 'w')
    for item in listdata:
        f.write(item+'\n')
        
def readFile(filepath):
    with open(filepath, 'r') as f:
        return f.read()

def extract_sents(text):
    text = remove_stopwords(text)
    res = []
    sents = sent_tokenize(text.strip())
    for sent in list(set(sents)):
        sent_tokens = nltk.word_tokenize(sent)
        joined_sent = ' '.join(sent_tokens)
        res.append(joined_sent)
    return res
    

def remove_punctuation(sent):
    translator = str.maketrans('', '', string.punctuation.replace('_', ''))
    return sent.translate(translator)
    
    
def text_preprocessor(text):
    text = remove_punctuation(remove_stopwords(text.lower()))
    return text
    
def remove_stopwords(sent):
    stop_words = set(nltk.corpus.stopwords.words('english'))
    word_tokens = nltk.word_tokenize(sent)
    filtered_sentence = [w for w in word_tokens if w not in stop_words]
    return " ".join(filtered_sentence)

def remove_bracket(sent):
    sent = sent.replace('(','').replace(')','')
    return sent

# def get_svo(sent):
#     text = nlp(sent)
#     return textacy.extract.subject_verb_object_triples(text)



def process_abbreviation(sent):
    for abbr in abbrs:
        if re.search(abbr, sent):
            sent = re.sub(abbr, abbrs[abbr], sent)
    return sent