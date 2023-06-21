import subprocess
from icecream  import ic
import os
import logging
import shlex
from config import DIFF_OUT_DIR


logger = logging.getLogger(__name__)


class GumTreeRunner:
    @staticmethod
    def run_gumtree_on_commit(repo, hexsha, patch_parser):
        diff_result = f'{DIFF_OUT_DIR}{hexsha}-gumtree-diff-1.json'
        
        try:
            after_path,before_path = patch_parser.get_modified_func_code()
            if after_path == '' or before_path == '':
                return
        except Exception as e:
            ic(e)
            return
        return GumTreeRunner.run_gumtree_on_file_pairs(before_path, after_path, diff_result)
    
    
    @staticmethod
    def run_gumtree_on_file_pairs(file_a, file_b, diff_result):
        if os.path.exists(diff_result):
            return
        base_cmd = f"gumtree textdiff -f json {file_a} {file_b} -o {diff_result}"
        logger.info(f"Execute: {base_cmd}")
        call_gumtree = subprocess.Popen(shlex.split(base_cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = call_gumtree.communicate()
        if out:
            logger.info(f"stdout: {out.decode()}")
        if err:
            err_headline = err.decode().split("\n", 1)[0]
            logger.warning(f"stderr: {err_headline}")

            call_gumtree.kill()
            return file_a,''

        return file_a,diff_result