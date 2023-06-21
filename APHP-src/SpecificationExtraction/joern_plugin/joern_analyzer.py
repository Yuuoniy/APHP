import contextlib
import json
from icecream import ic
import jsonschema
import networkx as nx
import os
from networkx.drawing import nx_agraph
from config import DUMP_NODE_INFO_SCRIPT_PATH,GET_CONTROL_STRUCT_SCRIPT_PATH,DUMP_DEP_INFO_SCRIPT_PATH


class JoernDataAnalyzer:
    def __init__(self):
        self.current_dir = os.path.dirname(os.path.realpath(__file__))
    
    def workflow(self,source_file,bin_file,graph_dir,tmpdir):
        self.joern_parse_to_get_cpg(source_file,bin_file)
        self.dump_annotated_cfg(bin_file,graph_dir,tmpdir)


    def dump_annotated_cfg(self, bin_file,graph_dir,tmpdir='/tmp/after.txt'):
        graph_path = os.path.join(graph_dir,'1-cfg.dot')
        if os.path.exists(graph_path):
            return 
        self.joern_dump_graph(bin_file,graph_dir)
        
        
        # run joern script to get needed info
        self.get_nodes_info(bin_file,tmpdir)
        self.get_control_struct_info(bin_file)
        
        
        id_lineNumber_mapping = self.get_id_lineNumber_mapping(tmpdir)

        
        # annotate the graph: lineNumber to node, condition to edge
        self.annotate_lineNumber_to_node_in_graph(id_lineNumber_mapping, graph_path)
        self.annotate_condition_to_edge_in_graph(graph_path)
        ic(graph_path)
        
    
    @classmethod
    def joern_parse_to_get_cpg(cls,source_file,bin_file):
        cmd = f'joern-parse  {source_file} -o {bin_file} > /dev/null 2>&1'
        # ic(cmd)
        os.system(cmd)



    def joern_dump_graph(self,bin_file,graph_dir):
        if os.path.exists(graph_dir):
            os.system(f'rm -rf {graph_dir}')
        cmd1 = f'joern-export  --repr cfg {bin_file} --out {graph_dir} > /dev/null 2>&1'
        ic(cmd1)
        os.system(cmd1)

    def get_nodes_info(self,bin_file,nodes_info_file='/tmp/node_info.json'):
        cmd = f"joern --script {DUMP_NODE_INFO_SCRIPT_PATH} --params cpgFile={bin_file},outFile={nodes_info_file} > /dev/null 2>&1"
        ic(cmd)
        os.system(cmd)

    def get_control_struct_info(self,bin_file,control_struct_data_path='/tmp/control_struct_data.log'):
        cmd = f"joern --script {GET_CONTROL_STRUCT_SCRIPT_PATH} --params cpgFile={bin_file},outFile={control_struct_data_path} > /dev/null 2>&1"
        ic(cmd)
        os.system(cmd)
    
    @classmethod
    def get_dependency_info(cls,bin_file,func,code,outfile):
        if os.path.exists(outfile):
            return
        
        cmd = f"joern --script {DUMP_DEP_INFO_SCRIPT_PATH} --params cpgFile={bin_file},func={func},code={code},outFile={outfile} > /dev/null 2>&1"
        # ic(cmd)
        # print(cmd)
        os.system(cmd)

    def get_id_lineNumber_mapping(self,nodes_info_file):
        ic(nodes_info_file)
        nodes_data = json.load(open(nodes_info_file))
        id_lineNumber_mapping = {}
        for node in nodes_data:
            with contextlib.suppress(KeyError):
                id_lineNumber_mapping[str(node['id'])] = node['lineNumber']
        # ic(len(id_lineNumber_mapping))
        return id_lineNumber_mapping


    def annotate_lineNumber_to_node_in_graph(self,id_lineNumber_mapping, graph_path):
        G = nx.drawing.nx_agraph.read_dot(graph_path)
        for node in G.nodes:
            # set node attributes
            lineNumber = id_lineNumber_mapping[node]
            G.nodes[node]['lineNumber'] = lineNumber
        # save
        nx.drawing.nx_agraph.write_dot(G, graph_path)
        ic(graph_path)


    def annotate_condition_to_edge_in_graph(self,in_graph_path,control_struct_data_path='/tmp/control_struct_data.log'):
        '''
        control data format
        {"lineNumber":18,"condition":["!hcd"],"lineNumbersWhenTrue":[19,19,19,19,19]}
        {"lineNumber":31,"condition":["ret < 0"],"lineNumbersWhenTrue":[31,32,32,33,33,33]}
        '''

        label = ""
        G = nx.drawing.nx_agraph.read_dot(in_graph_path)
        nx.set_edge_attributes(G, label, "label")

        data = open(control_struct_data_path,'r').read().splitlines()
        control_data = [json.loads(line) for line in data]
        nodes = list(filter((lambda n: G.out_degree(n) == 2),list(G.nodes)))
        print(len(nodes))
        for node in nodes:
            print(G.nodes[node])
            # get successors
            lineNumber = int(G.nodes[node]['lineNumber'])
            successors = list(G.successors(node))
            for condition_item in control_data:
                if condition_item['lineNumber'] == lineNumber:
                    print(condition_item)
                    for successor in successors:

                        if int(G.nodes[successor]['lineNumber']) in condition_item['lineNumbersWhenTrue']:
                            # add label to edge

                            print(node,successor)

                            G[node][successor]['0']['label'] = 'T'
                            print(G.edges[node,successor,'0'])
                        else:
                            G[node][successor]['0']['label'] = 'F'
        nx.drawing.nx_agraph.write_dot(G,in_graph_path)

                # get item from control_data with lineNumber
