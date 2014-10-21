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
OUTFILE_FILE = ''

PROPERTIES = {
    'token_mode': 'infinite',
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

r_parse = re.compile('^' + re.escape(taskname) + r'\.(\d+)(p?)-(\d+)\.in$')
def parse_testcase(path):
    m = r_parse.match(os.path.basename(path))
    if not m:
        return
    return int(m.group(1)), m.group(2) == 'p', map(int, m.group(3))


# Testcases, list of dirs, test filters and test parsers
# Test filter is a regex that should match an input file
# Test parser is a callable that is given an input file and should return a
# tuple (testcase number, is it public, a list of testgroups it belongs to,
# or None to skip the given file
# [(str, str, (int, bool, [int]) {filename})]
TESTS = (
    (TEST_DIR, r_parse, parse_testcase),
)


# [str]
RUN_COMMANDS = (
)
