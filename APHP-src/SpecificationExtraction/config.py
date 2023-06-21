import configparser
import os

APHP_SRC_DIR = "/root/APHP/APHP-src"
CORENLP_PATH = '/root/APHP/tools/stanford-corenlp-4.4.0'
TREE_SITTER_C_PATH  = "/root/APHP/tools/tree-sitter-c"
CPU_COUNT = 24

cp = configparser.RawConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
cp.read(f'{APHP_SRC_DIR}/config/config.cfg')

desc_tags_prefixes = cp.getlist('ARR','prefixes')

EXTRACTED_SPEC_DIR = cp.get('DATA_PATH','extracted_specs')


DIFF_LEFT_DIR =  f"{APHP_SRC_DIR}/SpecificationExtraction/intermediate_data/patch_diff/before/"
DIFF_RIGHT_DIR =  f"{APHP_SRC_DIR}/SpecificationExtraction/intermediate_data/patch_diff/after/"
DIFF_OUT_DIR = f"{APHP_SRC_DIR}/SpecificationExtraction/intermediate_data/patch_diff/diff/"

# if not exist, mkdir
if not os.path.exists(EXTRACTED_SPEC_DIR):
    os.makedirs(EXTRACTED_SPEC_DIR)
if not os.path.exists(DIFF_LEFT_DIR):
    os.makedirs(DIFF_LEFT_DIR)
if not os.path.exists(DIFF_RIGHT_DIR):
    os.makedirs(DIFF_RIGHT_DIR)
if not os.path.exists(DIFF_OUT_DIR):
    os.makedirs(DIFF_OUT_DIR)


DUMP_NODE_INFO_SCRIPT_PATH = f"{APHP_SRC_DIR}/SpecificationExtraction/joern_plugin/dump_node.sc"
GET_CONTROL_STRUCT_SCRIPT_PATH = f"{APHP_SRC_DIR}/SpecificationExtraction/joern_plugin/get_control_structure.sc"
DUMP_DEP_INFO_SCRIPT_PATH = f"{APHP_SRC_DIR}/SpecificationExtraction/joern_plugin/get_dependent_call.sc"


JOERN_JSON_DATA = f"{APHP_SRC_DIR}/SpecificationExtraction/intermediate_data/joern/json"
JOERN_BIN_DATA = f"{APHP_SRC_DIR}/SpecificationExtraction/intermediate_data/joern/bin"




# bug detection data: cfg, joern bin, xxx.
