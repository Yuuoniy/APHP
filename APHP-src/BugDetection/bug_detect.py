import traceback
import pandas as pd
import os
from icecream import ic
from modules.detect_wrapper import detectWrapper
import click
from config import DETECT_DATA_ROOT, DETECT_SPEC_PATH



def test_runner():
    specs = pd.read_csv(DETECT_SPEC_PATH)
    specs = specs.dropna()
    ic(specs.head)
    for i,spec in specs.iterrows():
        ic(spec)
        runner = detectWrapper(spec)
        runner.detect_bug_for_one_spec()


def test_one_spec_for_signle_func(test_func,target_API='')->bool:
    try:
        spec = get_spec_by_target_API(target_API).iloc[0]
        print(f"Testing specification for function {test_func}: {spec.to_dict()}")
        runner = detectWrapper(spec)
        runner.preprocess_one(test_func)
        return runner.detect_bug_in_one_func(test_func)
    except Exception as e:
        traceback.print_exc()
        ic(e)
        return False



def test_for_one_spec(target_API)->bool:
    specification = {
        'repo_name':'kernel',
        'target_API':'usb_create_hcd',
        'post_operation':'usb_put_hcd',
        'critical_var_role':'retval',
        'pre_condition':'success',
        'post_condition':'error'
    }
    print("detecting violations for specification: ",specification)
    runner = detectWrapper(specification)
    runner.detect_bug_for_one_spec()
    


def get_spec_by_target_API(api):
    try:
        specs = pd.read_csv(DETECT_SPEC_PATH)
        return specs[specs['target_API']==api]
    except Exception as e:
        traceback.print_exc()
        


@click.group()
def cli():
    click.echo("[Bug Detection Module]")
    
    
@cli.command("test_for_one_spec")
@click.argument('api')
def test_rule(api):
    test_for_one_spec(api)


# python main.py test_spec_for_one_func {target_API} {target_func}
@cli.command("test_spec_for_one_func")
@click.argument('target_api')
@click.argument('target_func')
def test_rule_for_one_func(target_api,target_func):
    test_one_spec_for_signle_func(target_func,target_api)




@cli.command("test_repo")
@click.argument('repo', default='kernel')
@click.option('--spec_path', default=DETECT_SPEC_PATH)
def run_on_repo(repo,spec_path):
    try:
        specs = pd.read_csv(spec_path)
        specs = specs.dropna()
        specs = specs[specs['repo_name']==repo]
        for i,spec in specs.iterrows():
            print("Testing violations for:\n", spec.to_dict())
            detect_wrapper = detectWrapper(spec)
            detect_wrapper.detect_bug_for_one_spec()
    except Exception as e:
        traceback.print_exc()
        ic(e)
        return False


if __name__ == '__main__':
    cli()
