import tree_sitter_helper
parser = tree_sitter_helper.tree_sitter_init()

class DiffParser:
    def __init__(self,repo,hexsha):
        self.hexsha = hexsha
        self.repo = repo
        self.APH_type = '' # value: call / check
        
    
    def get_inserted_func_calls(self):
        commit = self.repo.get_commit(self.hexsha)
        func_calls = []
        func_names = []
        for modified_file in commit.modified_files:
            added = modified_file.diff_parsed['added']
            for i in added:
                func,args,code = tree_sitter_helper.get_func_name_and_args(i[1].strip())
                if func:
                    func_calls.append((func, args, code))
                    func_names.append(func)
        return func_calls
    
    
    def get_APH_type_with_raw_diff(self) -> str:
        commit = self.repo.get_commit(self.hexsha)
        funcs = []
        for modified_file in commit.modified_files:
            added = modified_file.diff_parsed['added']
            for i in added:
                tree = parser.parse(bytes(i[1].strip(), "utf8"))
                checks = tree_sitter_helper.find_node_by_type(tree, "if_statement")
                if checks:
                    self.APH_type = 'check'
        if len(self.get_inserted_func_calls()):
            self.APH_type = 'call'
        return self.APH_type

    
    def get_inserted_checks(self):
        # XXX only consider the first check statement
        commit = self.repo.get_commit(self.hexsha)
        funcs = []
        for modified_file in commit.modified_files:
            added = modified_file.diff_parsed['added']
            for i in added:
                tree = parser.parse(bytes(i[1].strip(), "utf8"))
                if checks := tree_sitter_helper.find_node_by_type(tree, "if_statement"):
                    return tree_sitter_helper.get_condition_from_if_statement_node(checks[0],i[1].strip())
        return ''
