import networkx as nx
import tree_sitter_helper
# from rich.console import Console
from icecream import ic

parser = tree_sitter_helper.tree_sitter_init()



# console = Console()

def assignement_node_id_by_label(G,func):
    # print(G,func)
    labels = nx.get_node_attributes(G, "label")
    func = f' = {func}'
    return next(((id, label[:-1].split(',', 1)[1]) for id, label in labels.items() if func in label and '<operator>.assignment' in label), (None, None))

def callsite_node_id_by_label(G, func):
    labels = nx.get_node_attributes(G, "label")
    func = f'({func},'
    return next(((id, label[:-1].split(',', 1)[1]) for id, label in labels.items() if func in label), (None, None))


def get_assignment_use_var_as_right_value(G,var):
    labels = nx.get_node_attributes(G, "label")
    exprs = []
    for id, label in labels.items():
        if '<operator>.assignment' in label:
            stmt = label.split(',',1)[1][:-1]
            right = get_assignment_right_variable(stmt)
            if right==var:
                exprs.append(stmt)
    return exprs

# hdmi->cec_dev = &cec_pdev->dev; var = cec_pdev
def get_assignment_use_var_as_struct_of_right_value(G, var):
    labels = nx.get_node_attributes(G, "label")
    exprs = []
    for id, label in labels.items():
        if '<operator>.assignment' in label:
            stmt = label.split(',', 1)[1][:-1]
            if '(' in stmt:
                continue
            right = get_assignment_right_variable(stmt)
            if f"{var}->" in right:
                exprs.append(stmt)
    return exprs


def get_left_vals_in_assignment_exprs(exprs):
    return [get_assignment_left_variable(i) for i in exprs]

def get_first_arg_var(slice):
    if not slice.endswith(';'):
        slice += ';'
    tree = parser.parse(bytes(slice, "utf8"))
    arg_list = tree_sitter_helper.find_node_by_type(tree, "argument_list")
    idents = tree_sitter_helper.find_node_by_type(arg_list[0], "identifier")
    return tree_sitter_helper.get_node_content(
            idents[0], slice) # if is struct, only return the struct name, not field.


# special cases: rc = snd_card_new(&tpacpi_pdev->dev,
			#   alsa_index, alsa_id, THIS_MODULE,
			#   sizeof(struct tpacpi_alsa_data), &card);.
def extract_arguments(node):
    if node.type in ['sizeof_expression', 'identifier']:
        return [node.text.decode('utf-8')]
    # Recursively traverse the children of the node
    arguments = []
    for child in node.children:
        arguments += extract_arguments(child)
    return arguments
    

def get_pos_arg_var(pos,code_slice):
    pos = int(pos[-1:])
    code_slice = code_slice.replace('\\n', '').replace('\\t', '')
    if not code_slice.endswith(';'):
        code_slice += ';'
    tree = parser.parse(bytes(code_slice, "utf8"))
    
    # Find the function call node
    function_call_node = tree_sitter_helper.find_node_by_type(tree, "call_expression")[0]

    # Extract the arguments from the function call node
    arguments = []
    for argument_node in function_call_node.children[1:]:
        arguments += extract_arguments(argument_node)
    # ic(arguments)
    return arguments[pos]
    
    
def get_func_call(slice):
    tree = parser.parse(bytes(slice, "utf8"))
    calls = tree_sitter_helper.find_node_by_type(tree, "call_expression")
    func = [tree_sitter_helper.get_node_content(call.child_by_field_name("function"), slice) for call in calls]

    func = list(filter(tree_sitter_helper.remove_log_func, func))
    return func


def node_id_by_label(G,func):
    labels = nx.get_node_attributes(G, "label")
    func = f'({func},'
    for id, label in labels.items():
        if func in label:
            return id



def get_assignment_left_variable(slice):
    if not slice.endswith(';'):
        slice += ';'
    tree = parser.parse(bytes(slice, "utf8"))
    idents = tree_sitter_helper.find_node_by_type(tree, "assignment_expression")
    
    return tree_sitter_helper.get_node_content(
            idents[0].child_by_field_name("left"), slice
        )

def get_assignment_right_variable(slice):
    if not slice.endswith(';'):
        slice += ';'
    tree = parser.parse(bytes(slice, "utf8"))
    idents = tree_sitter_helper.find_node_by_type(tree, "assignment_expression")
    try:
        # this may be out of index
        return tree_sitter_helper.get_node_content(
                idents[0].child_by_field_name("right"), slice
            )
    except Exception as e:
        print('get_assignment_right_variable error')
        # ic(slice,e)
        return 'XXXXX'


def get_var_scope(code,var):
    # value = Local,Gloabl,Para
    scope = ''
    if check_variable_is_para(code, var):
        return 'Para'
    elif check_variable_is_local(code, var):
        return 'Local'
    else:
        return 'Global'
    
def check_variable_is_local(code, var):
    return var in tree_sitter_helper.get_local_vars(code)

def check_variable_is_para(code, var):
    return var in tree_sitter_helper.get_func_paras(code)

def get_return_node(G,path):
    return_node = G.nodes[path[-2]]
    if 'RETURN' not in return_node['label']:
        return_node = G.nodes[path[-1]]
    return return_node

def print_return_node(return_node):
    label = return_node['label'].split(',',1)[1][:-1].lower()
    # ic(label)

def print_return_node_in_path(G,path):
    return_node = get_return_node(G,path)
    print_return_node(return_node)


def check_is_error_path(G,path):
    return_node = get_return_node(G,path)
    ret_label = return_node['label'].split(',',1)[1][:-1].lower()
    print(ret_label)
    return '-' in ret_label or 'err' in ret_label or 'null' in ret_label

def check_is_non_error_path(G,path):
    return_node = get_return_node(G,path)
    ret_label = return_node['label'].split(',',1)[1][:-1].lower()
    return '0' in ret_label

def check_is_uncertain_path(G,path):
    return_node = get_return_node(G,path)
    ret_label = return_node['label'].split(',')[1][:-1].lower().split()[-1]
    # ic(ret_label)
    return 'ret' in ret_label or 'rc' in ret_label

def check_is_escaped_path(G,path,var):
    return_node = get_return_node(G,path)
    ret_label = return_node['label'].split(',')[1][:-1].lower().split()[-1]
    return var == ret_label

def format_path(G,path):
    labels = [G.nodes[x]['label'] for x in path]
    # print('->'.join(labels))
    return '->'.join(labels)




