import difflib
import itertools

class APIPairChecker:
    def __init__(self):
        self.main_suffix = ['init', 'alloc', 'lock', 'start', 'open', 'get', 'new','strdup','create','connect','add']
        self.opposite_words = [['add', 'del'], ['enable', 'disable'], ['register', 'unregister'], ['get', 'put'],['prepare','unprepare'],['new','free']]


    def find_api_pair(self, post_api, api_list):
        # check pairs with high confidence
        if api_pair := self.find_api_pair_strong(post_api,api_list):
            return api_pair
        return self.find_api_pair_weak(post_api,api_list)



    def find_api_pair_weak(self, post_api, api_list):
        api_pair = 'unknown'
        max_ratio = 0
        for api in api_list:
            for suffix in self.main_suffix:
                if suffix in api:
                    ratio = difflib.SequenceMatcher(None, post_api, api).ratio()
                    if ratio > max_ratio:
                        max_ratio = ratio
                        api_pair = api
        return api_pair

    def find_api_pair_strong(self, post_api, api_list):
        return next(
        (
            api
            for api in api_list
            if self.check_apis_pairs_with_high_confidence(api, post_api)
        ),
        None,
    )



    def check_apis_pairs_with_high_confidence(self, api_a, api_b):
        api_list = api_a.split('_')
        post_op_list = api_b.split('_')

        # they should have the same length
        if len(api_list) != len(post_op_list):
            return False

        # get unique token in api_a and api_b
        api_a_unique = list(set(api_list) - set(post_op_list))
        api_b_unique = list(set(post_op_list) - set(api_list))

        # they should have same length
        if len(api_a_unique) != len(api_b_unique):
            return False

        # for each unique token in api_a, the opposite token should be in api_b
        for token, words in itertools.product(api_a_unique, self.opposite_words):
            if token in words:
                return words[0] in api_b_unique or words[1] in api_b_unique
    