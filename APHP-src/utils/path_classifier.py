import pdb
import networkx as nx
from icecream import ic

class PathClassifier:
    # input: G
    # output: error paths and non-error paths, escape path.
    def __init__(self,G) -> None:
        self.G = G
        self.ret_labels = self.get_retvals()
        self.success = []
        self.error = []
        # self.critical_var = critical_var
        # return values indicate error and success.
    
    
    def workflow(self):
        self.get_retvals()
        self.classify_paths_by_retvals()
        return self.success, self.error
    
    def classify_paths_by_retvals(self):
        self.success = []
        self.error = []
        
        # rule1: if has return 0; then other return values is error values. (Linux kernel)
        if '0' in self.ret_labels:
            self.success.append('0')
            # the remianing are error except 0
            self.error.extend([x for x in self.ret_labels if x != '0'])
            return
        
        # rule2: if has return null, then other return values is success. 
        if 'null' in self.ret_labels:
            self.error.append('null')
            # the remianing are error except 0
            self.success.extend([x for x in self.ret_labels if x != 'null'])
            return
        
        for ret_label in self.ret_labels:
            if '-' in ret_label or 'err' in ret_label:
                self.error.append(ret_label)
            else:
                self.success.append(ret_label)
                
                
    def get_retvals(self):
        return_nodes =  [n for n in self.G.nodes() if '(RETURN' in self.G.nodes[n]['label']]


        self.ret_labels = [self.G.nodes[n]['label'] for n in return_nodes]
        self.ret_labels = [self.get_retval(x) for x in self.ret_labels]
        self.ret_labels = list({x for x in self.ret_labels if x != ''})
        # ic(self.ret_labels)
        
    
    @classmethod
    def get_retval(cls,return_node_label):
        return return_node_label.split(',', 2)[-1][:-2].lower().replace(" ", "").replace("\\t", "")[6:]
    
    @classmethod
    def check_is_path_type(cls, G, success_vals,error_vals,  path):
        return_node = G.nodes[path[-2]]
        if 'RETURN' not in return_node['label']:
            return_node = G.nodes[path[-1]]
        ret_label = cls.get_retval(return_node['label'])
        # ic(ret_label,success_vals,error_vals)
        if ret_label in error_vals:
            return 'error'
        elif ret_label in success_vals:
            return 'success'
        return 'unknown'