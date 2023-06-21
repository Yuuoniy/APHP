from logging import critical
import traceback
import networkx as nx
from icecream import ic
import os
import timeout_decorator
import sys
sys.path.append('/root/bug-tools/APHP-ArtifactEvaluation/APHP-src')
# import cfg_analyzer
# sys.path.append('../joern_plugin')
# import analyzer4joern
import joern_plugin.joern_analyzer as joern_analyzer
from utils.path_classifier import PathClassifier


ic.configureOutput(includeContext=True)

def node_id_by_label(G,func):
    labels = nx.get_node_attributes(G, "label")
    func = f'{func}'
    for id, label in labels.items():
        if func in str(label):
            return id

def format_path(G,path):
    ic(path)
    labels = [G.nodes[x]['label'] for x in path]
    ic('->'.join(labels))
    return '->'.join(labels)



class pathCondCollector:
    def __init__(self,hexsha, source_code_file, bin_file, target_API,post_operation):
        self.hexsha = hexsha
        self.source_code_file = source_code_file
        self.bin_file = bin_file
        
        self.cfg_path = ''
        self.graph = ''
        self.critical_node = ''
        self.target_API = target_API
        self.critical_var_role = ''
        self.post_operation = post_operation
        self.post_cond = ''
        self.whole_path = []
        self.data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'code_data',self.hexsha)
        
    
    @timeout_decorator.timeout(500)    
    def collect_conds(self):
        self.preprocess()
        self.get_patch_effected_path()
        self.get_post_condition()
        return self.post_cond
        
    
    # generate CFG and simplify it.
    def preprocess(self):
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)
        self.after_cfg_dir = os.path.join(self.data_dir,"after-cfg")
        ic(self.after_cfg_dir)
        
        # dump cfg
        joernAnalyzer = joern_analyzer.JoernDataAnalyzer()
        joernAnalyzer.dump_annotated_cfg(self.bin_file,
            self.after_cfg_dir)
        
        self.graph = nx.drawing.nx_agraph.read_dot(f"{self.after_cfg_dir}/1-cfg.dot")
        ic(f"{self.after_cfg_dir}/1-cfg.dot")
        
    def get_patch_effected_path(self):
        forward_path = self.forward_explore()
        backword_path = self.backword_explore()
        format_path(self.graph,forward_path)
        format_path(self.graph,backword_path)
        self.whole_path = forward_path + backword_path
        # ic(self.whole_path)
        # self.get_condition_node(all_path)
        # merge paths
    
    def forward_explore(self):
        source = node_id_by_label(self.graph,self.target_API)
        target = node_id_by_label(self.graph,self.post_operation)
        print(source)
        for path in list(nx.all_simple_paths(self.graph, source=source, target=target)):
        # for path in list(nx.shortest_path(self.graph, source=source, target=target)):
            # print(path)
            return path
    
    def backword_explore(self):
        source = node_id_by_label(self.graph,self.post_operation)
        target = node_id_by_label(self.graph,'METHOD_RETURN')
        # choose the shorest path
        for path in list(nx.all_simple_paths(self.graph, source=source, target=target)):
        # for path in list(nx.shortest_path(self.graph, source=source, target=target)):
            # print(path)
            return path
    
    def get_post_condition(self):
        
        classifier =  PathClassifier(self.graph)
        success_vals,err_vals = classifier.workflow()
        self.post_cond = PathClassifier.check_is_path_type(self.graph,success_vals,err_vals,self.whole_path)
        
        ic(success_vals,err_vals,self.post_cond)
        
    
def test():
    path = '/root/bug-tools/commitAnalyzer/oxu_create-usb_create_hcd.dot'
    G = nx.drawing.nx_agraph.read_dot(path)
    target_API = 'usb_create_hcd'
    post_operation = 'usb_put_hcd'
    critical_var = 'hcd'
    collect = pathCondCollector(graph=G,target_API=target_API,post_operation=post_operation)
    collect.collect_conds()
    
    
    
if __name__ == '__main__':
    test()