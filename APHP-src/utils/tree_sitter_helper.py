from re import I
from tree_sitter import Language, Parser
from icecream import ic
from typing import List
from config import TREE_SITTER_C_PATH

LOG_FUNC = ['mtk_v4l2_err','dev_err','dev_err_probe','pr_debug']


def tree_sitter_init():
    Language.build_library(
        # Store the library in the `build` directory
        "build/my-languages.so",
        # Include one or more languages
        [TREE_SITTER_C_PATH],
    )

    C_LANGUAGE = Language("build/my-languages.so", "c")
    parser = Parser()
    parser.set_language(C_LANGUAGE)
    return parser


parser = tree_sitter_init()

# code samples
# "derived_name = kstrndup(clk_name, endp - clk_name,GFP_KERNEL);if (!derived_name)return NULL;"
# "node_info->vdev_port.name = kstrdup_const(name, GFP_KERNEL);if (!node_info->vdev_port.name) return -1;"
def get_checked_function(node, code):
    ident_str_arr = get_identifier_from_if_statement(node, code)
    func_value_map = get_func_with_return_value_assignment(node, code)
    return [func for func in func_value_map if func_value_map[func] in ident_str_arr]





# get function with return value assignment
# return : return value ident and function name
def get_func_with_return_value_assignment(node, code):
    ass_nodes = find_node_by_type(node, "assignment_expression")
    func_value_map = {}
    for i in ass_nodes:
        if i.child_by_field_name("right").type != "call_expression":
            continue
        identifier = get_node_content(i.child_by_field_name("left"), code)
        func = get_node_content(
            i.child_by_field_name("right").child_by_field_name("function"), code
        )
        func_value_map[func] = identifier
    return func_value_map


def get_func_with_return_value_assignment_multiple_values(node, code):
    func_value_map = {}
    
    ass_nodes = find_node_by_type(node, "assignment_expression")
    for i in ass_nodes:
        if i.child_by_field_name("right").type != "call_expression":
            continue
        identifier = get_node_content(i.child_by_field_name("left"), code)
        if identifier.startswith("*"):
            identifier = identifier[1:]
        func = get_node_content(
            i.child_by_field_name("right").child_by_field_name("function"), code
        )
        if func in func_value_map:
            func_value_map[func].append(identifier)
        else:
            func_value_map[func] = [identifier]
    
    # BN_CTX *bnctx = BN_CTX_new_ex(ossl_ec_key_get_libctx(eckey));        
    inits = find_node_by_type(node, "init_declarator")
    for init in inits:
        init_left = init.child_by_field_name("declarator")
        init_right = init.child_by_field_name("value")
        #  and init_left.type == 'pointer_declarator'
        if init_right.type == 'call_expression':
            var = get_node_content(init_left, code)
            func = get_node_content(init_right.child_by_field_name("function"), code)
            if var.startswith('*'):
                var = var[1:]
            if func in func_value_map:
                func_value_map[func].append(var)
            else:
                func_value_map[func] = [var]
                
    return func_value_map

def get_node_content(node, code):
    return code[node.start_byte : node.end_byte]


def get_identifier_from_if_statement(node, code):
    if_nodes = find_node_by_type(node, "if_statement")
    ident_str_arr = []

    for if_node in if_nodes:
        # ident_str_arr = find_node_by_type_and_get_content(if_node, "identifier", code)
        ident_str_arr += get_unary_expr_indent(
            find_node_by_type(if_node, "unary_expression"), code
        )

    return ident_str_arr


def get_unary_expr_indent(unary_nodes, code):
    return [get_node_content(node.child_by_field_name("argument"), code) for node in unary_nodes]


def parse_code(parser, slice):
    return parser.parse(bytes(slice, "utf8"))


# return value: array of content of the nodes
def find_node_by_type_and_get_content(node, node_type, code):
    cursor = node.walk()
    if type(node_type) == str:
        node_type = [node_type]
    node_str_lst = []
    while True:
        if cursor.node.type in node_type:
            node_str_lst.append(get_node_content(cursor.node, code))
        if not cursor.goto_first_child():
            while not cursor.goto_next_sibling():
                if not cursor.goto_parent():
                    return node_str_lst


def find_node_by_type(node, node_type):
    cursor = node.walk()
    if type(node_type) == str:
        node_type = [node_type]
    node_lst = []
    while True:
        if cursor.node.type in node_type:
            node_lst.append(cursor.node)
        if not cursor.goto_first_child():
            while not cursor.goto_next_sibling():
                if not cursor.goto_parent():
                    return node_lst


def find_node_by_field(node, field_name):
    cursor = node.walk()
    if type(field_name) == str:
        field_name = [field_name]
    node_lst = []
    while True:
        for _f in field_name:
            if child := cursor.node.child_by_field_name(_f):
                node_lst.append(child)
        if not cursor.goto_first_child():
            while not cursor.goto_next_sibling():
                if not cursor.goto_parent():
                    return node_lst

def find_node_by_field_and_get_content(node, field_name,code):
    cursor = node.walk()
    if type(field_name) == str:
        field_name = [field_name]
    node_str_lst = []
    while True:
        for _f in field_name:
            if child := cursor.node.child_by_field_name(_f):
                node_str_lst.append(get_node_content(child, code))
        if not cursor.goto_first_child():
            while not cursor.goto_next_sibling():
                if not cursor.goto_parent():
                    return node_str_lst



            
def get_local_vars(code):
    tree = parser.parse(bytes(code, "utf8"))
    funcs = find_node_by_type(tree,"declaration")
    # print(vars)
    return [get_node_content(find_node_by_type(x.child_by_field_name("declarator"), 'identifier')[0], code) for x in funcs]

#FIXME
def get_func_paras(code):
    tree = parser.parse(bytes(code, "utf8"))
    funcs = find_node_by_type(tree,"function_declarator")
    if len(funcs) == 0:
        return []
    idents = find_node_by_type(funcs[0].child_by_field_name('parameters'), "identifier")
    return [get_node_content(ident, code) for ident in idents]



def is_autofree_var(code,var):
    tree = parser.parse(bytes(code, "utf8"))
    declars = find_node_by_type(tree,"declaration")
    for declar in declars:
        line = get_node_content(declar, code)
        if var in line:
            if 'autofree' in line:
                return True
            if 'g_auto' in line:
                return True
    return False

def get_assignment_left_variable(slice):
    if not slice.endswith(';'):
        slice += ';'
    tree = parser.parse(bytes(slice, "utf8"))
    idents = find_node_by_type(tree, "assignment_expression")
    return get_node_content(
            idents[0].child_by_field_name("left"), slice
        )

def get_func_call(slice):
    # if slice is list
    tree = parser.parse(bytes(slice, "utf8"))
    calls = find_node_by_type(tree, "call_expression")
    func = [get_node_content(call.child_by_field_name("function"), slice) for call in calls]

    func = list(filter(remove_log_func,func))
    return sorted(set(func), key=func.index)


def get_check_expr(slice):
    tree = parser.parse(bytes(slice, "utf8"))
    if_exprs = find_node_by_type(tree, "if_statement")
    return [get_node_content(expr.child_by_field_name("condition"), slice) for expr in if_exprs]



def get_goto_label(slice):
    tree = parser.parse(bytes(slice, "utf8"))
    gotos = find_node_by_type(tree, "goto_statement")
    return [get_node_content(goto.child_by_field_name("label"), slice) for goto in gotos]

def get_label_expr_in_code(slice):
    tree = parser.parse(bytes(slice, "utf8"))
    label_stats = find_node_by_type(tree, "labeled_statement")
    labels = [get_node_content(x.child_by_field_name("label"), slice) for x in label_stats]
    stats = [get_node_content(get_label_expr_one(x), slice) for x in label_stats]
    
    return dict(zip(labels, stats))


def get_label_expr_one(label_node):
    cursor = label_node.walk()
    cursor.goto_first_child()
    cursor.goto_next_sibling()
    cursor.goto_next_sibling()
    # stat = get_node_content(cursor.node, code)s
    return cursor.node

def get_goto_stat_by_label(slice, label):
    label_map = get_label_expr_in_code(slice)
    return label_map[label] if label_map.get(label) else ''


# example:
# input: 'close_candev(ndev)'
# output: ('close_candev', ['ndev'], 'close_candev(ndev)')
def get_func_name_and_args(slice):
    if not slice.endswith(';'):
        slice += ';'
    tree = parser.parse(bytes(slice, "utf8"))
    calls = find_node_by_type(tree, "call_expression")
    func = ''
    args = []
    code = ''
    for call in calls:
        func = get_node_content(
            call.child_by_field_name("function"), slice
        )
        args_node = call.child_by_field_name("arguments")
        for indent in find_node_by_type(args_node, "identifier"):
            indet = get_node_content(indent,slice)
            args.append(indet)
        code = get_node_content(call,slice)
    # pdb.set_trace()
    return func,args,code


    
def remove_log_func(func):
    return func not in LOG_FUNC

def get_func_name_from_def(code):
    tree = parser.parse(bytes(code, "utf8"))
    funcs = find_node_by_type(tree,"function_declarator")
    if len(funcs) == 0:
        return ''

    return get_node_content(funcs[0].child_by_field_name("declarator"), code)


def get_first_arg_var(slice):
    if not slice.endswith(';'):
        slice += ';'
    tree = parser.parse(bytes(slice, "utf8"))
    arg_list = find_node_by_type(tree, "argument_list")
    idents = find_node_by_type(arg_list[0], "identifier")
    return get_node_content(
            idents[0], slice) # if is struct, only return the struct name, not field.




def get_condition_from_if_statement_node(node,code):
    return get_node_content(node.child_by_field_name("condition"), code)


# FOR contol structure analysis
def parse_for_statement(slice):
    tree = parser.parse(bytes(slice, "utf8"))
    if_statement = find_node_by_type(tree, "for_statement")
    if len(if_statement) == 0:
        return ''
    initializer = if_statement[0].child_by_field_name("initializer").text.decode("utf8")
    condition = if_statement[0].child_by_field_name("condition").text.decode("utf8")
    update = if_statement[0].child_by_field_name("update").text.decode("utf8")
    return dict(initializer=initializer,condition=condition,update=update)

# contol structure analysis
def parse_while_statement(slice):
    tree = parser.parse(bytes(slice, "utf8"))
    while_statement = find_node_by_type(tree, "while_statement")
    if len(while_statement) == 0:
        return ''
    condition = while_statement[0].child_by_field_name("condition").text.decode("utf8")
    return dict(condition=condition)
    

def get_args_list_from_func_call(slice):
    if not slice.endswith(';'):
        slice += ';'
    tree = parser.parse(bytes(slice, "utf8"))
    arg_list = find_node_by_type(tree, "argument_list")
    args_var = []
    for arg in arg_list:
        idents = find_node_by_type(arg, "identifier")
        if len(idents) == 0:
            continue
        var = get_node_content(idents[0], slice) # if is struct, only return the struct name, not field.
        args_var.append(var)
    return  args_var

# cases
# ov.hEvent = CreateEvent(NULL, FALSE, FALSE, NULL);
# char *result = g_malloc0(size);
def get_retval_from_func_call(slice):
    if not slice.endswith(';'):
        slice += ';'
    tree = parser.parse(bytes(slice, "utf8"))
    # type 1 assignment
    assigns = find_node_by_type(tree, "assignment_expression")
    for assign in assigns:
        assign_left = assign.child_by_field_name("left")
        assign_right = assign.child_by_field_name("right")
        if assign_right.type == 'call_expression' and assign_left.type in ['identifier','field_expression']:
            return get_node_content(assign_left, slice)
    
    # type 2 init
    inits = find_node_by_type(tree, "init_declarator")
    for init in inits:
        init_left = init.child_by_field_name("declarator")
        init_right = init.child_by_field_name("value")
        if init_right.type == 'call_expression' and init_left.type == 'pointer_declarator':
            var = get_node_content(init_left, slice)
            if var.startswith('*'):
                var = var[1:]
            return var
    return ''



def get_retval_and_args_in_callsite(slice):
    return {'retval':get_retval_from_func_call(slice),'args':get_args_list_from_func_call(slice)}



def get_idents_in_expr(slice) -> List[str]:
    if not slice.endswith(';'):
        slice += ';'
    tree = parser.parse(bytes(slice, "utf8"))
    idents_node = find_node_by_type(tree,"identifier")
    idents =  [x.text.decode("utf-8") for x in idents_node]

    # get func name
    func,arg,code= get_func_name_and_args(slice)
    idents = [x for x in idents if x != func]

    return idents


# input: code slice, func name
# list of func callsites
# for exmaple: ['np = of_find_compatible_node(NULL, NULL, "ibm,opal-intc");']
# if ((fp = popen(command, "r")) == NULL)
# {
# 	fprintf(stderr, "%s: cannot launch shell command\n", argv[0]);
# 	return false;
# }
from typing import List
def get_func_callsite_from_code(code,func_name)-> List[str]:
    tree = parser.parse(bytes(code, "utf8"))
    calls = find_node_by_type(tree, "call_expression")
    callsites = []
    for call in calls:
        func_name_in_call = get_node_content(
            call.child_by_field_name("function"), code
        )
        if func_name_in_call == func_name:
            callsite = get_node_content(call, code)
            # ic(callsite)
            '''
            while((not callsite.endswith(';')) and call and call.parent):
                call = call.parent
                ic(callsite)
                callsite = get_node_content(call, code)
            '''
            if call.parent.type == 'assignment_expression':
                call = call.parent
                callsite = get_node_content(call, code)
            callsites.append(callsite)
    return callsites


# for infer the main api
# has bug. because one func only have one values
# func: list(value)
def get_return_value_assign_func_call(code, var):
    tree = parser.parse(bytes(code, "utf8"))
    # node = tree.get_root_node()
    func_retval_map = get_func_with_return_value_assignment_multiple_values(tree, code)
    # pdb.set_trace()
    return next((func for func, retvals in func_retval_map.items() if var in retvals), None)
    
    
def get_param_list_from_func_proto(func_proto):
    tree = parser.parse(bytes(func_proto, "utf8"))
    param_node = find_node_by_type(tree,"parameter_declaration")
    return [get_node_content(param, func_proto) for param in param_node]