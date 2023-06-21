import configparser
import os

APHP_DIR = "/root/APHP"
APHP_SRC_DIR = f"{APHP_DIR}/APHP-src"
CPU_COUNT = 24
CFG_TIMEOUT = 100

cp = configparser.RawConfigParser(converters={'list': lambda x: [i.strip() for i in x.split(',')]})
cp.read(f'{APHP_SRC_DIR}/config/config.cfg')


DETECT_WORK_ROOT = f"{APHP_SRC_DIR}/BugDetection"
DETECT_DATA_ROOT = f"{APHP_SRC_DIR}/BugDetection/intermediate_data"
DETECT_SPEC_PATH = f"{APHP_DIR}/data/sample_data/sample_specs_for_detecting.csv"
TREE_SITTER_C_PATH = f'{APHP_DIR}/tools/tree-sitter-c'

BUG_REPORT_DIR = f'{APHP_DIR}/data/BugReports'
BUG_REPORT_FILE = f'{BUG_REPORT_DIR}/bug_report.csv'

if not os.path.exists(DETECT_DATA_ROOT):
        os.mkdir(DETECT_DATA_ROOT)

if not os.path.exists(BUG_REPORT_DIR):
        os.mkdir(BUG_REPORT_DIR)

REPORT_RANKD_SCRIPT = f"{APHP_SRC_DIR}/scripts/report_ranker.py"