# coding: utf-8
import os
import re

taskname = os.path.basename(os.path.abspath(os.curdir))

# task title
TITLE = ''

TASK_DIR = r''

# where tests are stored
# str
TEST_DIR = r''

# where grader and headers are stored
# must have subdirs 'private' and 'public'
# str
API_DIR = r''

# [str]
#STATEMENT_LANGUAGES = ['lt']
# str
PRIMARY_STATEMENT = 'lt'
# str {language}
TASK_DESCRIPTION = os.path.join(TASK_DIR, taskname + '.pdf')

# time limit, s
TIME_LIMIT = 1

# memory limit, MB
MEMORY_LIMIT = 64

# input filename, empty for stdin
INPUT_FILE = ''

# output filename, empty for stdout
OUTPUT_FILE = ''

PROPERTIES = {
    'token_mode': 'infinite',
#    'token_gen_initial': 3,
#    'token_gen_number': 1,
#    'token_gen_interval': 20 * 60,
#    'token_gen_max': 3,
#    'token_max_number': 60,
#    'max_submission_number': 100,
#    'max_user_test_number': 100,
#    'min_submission_interval': 60,
#    'min_user_test_interval': 60,
#    'version': 'Default',
}


# int
TOTAL_POINTS = 100

def divide_equal(total, n):
    d, r = total // n, total % n
    return [d] * (n - r) + [d + 1] * r

# [int] {total, n}
POINTS = divide_equal

# [float]
#THRESHOLDS = []


def get_output_filename(filename):
    return os.path.splitext(filename)[0] + '.sol'

OUTPUT_FILENAME = lambda: get_output_filename

r_parse_simple = re.compile('^' + re.escape(taskname) + r'\.(s|g)(\d+)([a-z])\.in$')
def parse_testcase_simple(path):
    m = r_parse_simple.match(os.path.basename(path))
    if not m:
        return
    group = int(m.group(2))
    case = m.group(3)
    public = m.group(1) == 's'
    return (not public, group, case), public, [group]


r_parse_shared = re.compile('^' + re.escape(taskname) + r'\.(\d+)(p?)-(\d+)\.in$')
def parse_testcase_shared(path):
    m = r_parse_shared.match(os.path.basename(path))
    if not m:
        return
    case = int(m.group(1))
    public = m.group(2) == 'p'
    groups = map(int, m.group(3))
    return case, public, groups


# Testcases, list of dirs, test filters and test parsers
# Test filter is a regex that should match an input file
# Test parser is a callable that is given an input file and should return a
# tuple (testcase key, is it public, a list of keys for testgroups it belongs to),
# or None to skip the given file
# [(str, str, (*, bool, [*]) {filename})]
TESTS = (
#    (TEST_DIR, r_parse_simple, parse_testcase_simple),
    (TEST_DIR, r_parse_shared, parse_testcase_shared),
)


# [str]
RUN_COMMANDS = (
#    'cp {}/checker.cpp check/checker.cpp'.format(TEST_DIR),
#    'g++ -std=c++11 check/checker.cpp -o check/checker -O2 -static',
)
