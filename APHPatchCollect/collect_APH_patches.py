from git import Repo
from pydriller import *
import pandas as pd
import click
import configparser
from rich.progress import track
import os


# read config from files
cp = configparser.RawConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
cp.read('/root/bug-tools/APHP-ArtifactEvaluation/APHP-src/config/config.cfg')
keywords = cp.getlist('PATCH_COLLECT','keyword')
PATCH_DIR = cp.get('DATA_PATH','patch')
neg_keywords = ['revert']


class APHPatchCollector:
    def __init__(self,repo_name) -> None:
        self.repo_name = repo_name
        self.source_dir = cp.get('URL',repo_name)
        self.repo = Repo(self.source_dir)
        self.repo1 = Git(self.source_dir)
        self.commit_url = cp.get('COMMITURL',repo_name)
        self.get_APH_patches()
    
    
    def get_APH_patches(self):
        branch = cp.get('BRANCH',self.repo_name)
        print("Collecting patches potentially relted to APH bugs in" , self.repo_name, branch)
        patch_file_path = os.path.join(PATCH_DIR, f'APH_patches_{self.repo_name}_{branch}.csv')
        idlist = list(
                self.repo.iter_commits(
                    branch, max_count=999999, no_merges=True,
                )
            )
        df = pd.DataFrame()
        print(f"Processing all the patches to find suspects, total patch number is: {len(idlist)}")
        for i in track(idlist):
            patch = f"{self.commit_url}{i.hexsha[:12]}"
            if self.check_is_related_to_APH(i.hexsha[:12]):
                item = {"hexsha": i.hexsha[:12], "patch": patch, "summary": i.summary, "author": i.author.name}

                df_new_row = pd.DataFrame([item])
                df = pd.concat([df,df_new_row],ignore_index=True)
        print(f"Done, the collected patch is {len(df)}, save to file " + patch_file_path)
        df.to_csv(patch_file_path, index=False)

        
    def check_is_related_to_APH(self,hexsha):
        commit = self.repo.commit(hexsha)
        return bool((self.check_patch_description(commit.summary) and self.check_code_changes(hexsha)))
    

    def check_code_changes(self,hexsha):
        commit = self.repo1.get_commit(hexsha)
        if commit.files>2 or commit.insertions>10 or commit.deletions>10:
            return False

        # func-level check: no modification for func or too many funcs
        modified_func = []
        for f in commit.modified_files:
            modified_func.extend(method.name for method in f.changed_methods)
        
        return len(modified_func) >= 1 and len(modified_func) <= 2



    def check_patch_description(self, desc):
        desc = desc.lower()
        if any(keyword in desc for keyword in neg_keywords):
            return False
        return any((key in desc for key in keywords))
        


@click.group()
def cli():
    pass


@cli.command('one')
@click.argument('repo_name')
def collect_one_repo(repo_name):
    APHPatchCollector(repo_name)

 

# example: python get_api_misuse_commit.py one redis
if __name__ == '__main__':
    cli()

    



