# given a df which has a commit column, then get their message, api, etc
import os
import re
import string
import subprocess
import pandas as pd
from icecream import ic
import click
import sys
import extract_modules.extract_specs_from_patch as extract_specs_from_patch
from pydriller import Git
import click
from datetime import datetime
import numpy as np
import traceback
from config import EXTRACTED_SPEC_DIR,CPU_COUNT
from config import cp

ic.configureOutput(includeContext=True)

from pandarallel import pandarallel
pandarallel.initialize(progress_bar=False,nb_workers=CPU_COUNT,use_memory_fs=False,verbose=0)




def extract_spec_from_patch_one(repo,hexsha):
    extractor = extract_specs_from_patch.SpecExtractor(repo,hexsha)
    return extractor.extract_spec_from_patch_one()



def extract_spec_from_patch_batch(repo_name,infile, outfile):
    df = pd.read_csv(infile)
    df = df.dropna(axis=0, how='any')
    df = df.drop_duplicates(subset=['hexsha'], keep='first')
    
    cols = ['hexsha','target_API','post_op_name','type','variable_role','pre_condition','post_condition']
    specs_df = pd.DataFrame(columns=cols) 

    source_dir = cp.get('URL',repo_name)
    repo = Git(source_dir)


    specs_df[cols] = df.parallel_apply(lambda item: extract_spec_from_patch_one(repo,item['hexsha']), axis=1, result_type="expand")
    specs_df.to_csv(outfile, index=False)



    # print statistics information
    print('-'*20)
    print('repo_name:',repo_name)
    print('input file:',infile)
    print('output file:',outfile)
    print("#input patch", len(df))
    print("#output specs", len(specs_df))
    print('-'*20)



@click.group()
def cli():
    click.echo(f"[Extraction Specification Module]")



@cli.command("batch")
@click.argument("in_file")
@click.option("--out","out_file",default='')
def extract_rules_from_patchs(in_file,out_file):
    date = datetime.now().strftime('%m-%d')
    basefile = os.path.basename(in_file)

    if out_file == '':
        out_file =   os.path.join(EXTRACTED_SPEC_DIR, basefile.replace('.csv',f'-specs-{date}.csv')) 

    repo_name = 'kernel'
    
    extract_spec_from_patch_batch(repo_name,in_file,out_file)


@cli.command("one")
@click.argument('repo_name')
@click.argument('hexsha')
def one(repo_name,hexsha):
    source_dir = cp.get('URL',repo_name)
    repo = Git(source_dir)
    extract_spec_from_patch_one(repo, hexsha)


if __name__ == '__main__':
    cli()
    
    