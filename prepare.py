#!/usr/bin/env python3
# -*- coding: utf8 -*-
from __future__ import unicode_literals, print_function, division

import sys, os, re, shutil, yaml
from collections import defaultdict, OrderedDict
from zipfile import ZipFile
import tarfile

assert __name__ == '__main__'

if len(sys.argv) > 1:
    os.chdir(sys.argv[1])
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

import config

def copy(src, dst):
    print('copy', src, '->', dst)
    shutil.copyfile(src, dst)

def create_arc(dir, arcfile, type='tgz'):
    if type == 'tgz':
        f = tarfile.open(arcfile, 'w:gz')
        def add(f, path, rpath):
            f.add(path, rpath)
    elif type == 'zip':
        f = ZipFile(arcfile, 'w')
        def add(f, path, rpath):
            f.write(path, rpath)
    else:
        return
    with f:
        for root, dirs, files in os.walk(dir):
            i = 0
            while i < len(dirs):
                if dirs[i].startswith('.'):
                    del dirs[i]
                else:
                    i += 1
            for fn in files:
                if fn.startswith('.'):
                    continue
                path = os.path.join(root, fn)
                rpath = os.path.relpath(path, dir)
                print(type, path, '->', '{}:{}'.format(arcfile, rpath))
                add(f, path, rpath)

def mkdir(dir):
    if not os.path.exists(dir):
        os.mkdir(dir)

def get_value(getter, kwargs=None):
    if kwargs is None:
        kwargs = {}
    if callable(getter):
        value = getter(**kwargs)
    else:
        value = getter
    return value

def get_config_value(name, kwargs=None, default=None):
    getter = getattr(config, name, default)
    return get_value(getter, kwargs)

task_name = os.path.basename(os.path.abspath('.'))

test_dir = get_config_value('TEST_DIR')


def get_test_case_defs():
    defs = get_config_value('TESTS')
    return defs


class TestCase(object):
    def __init__(self, inputfile=None, outputfile=None, public=False, index=0):
        self.inputfile = inputfile
        self.outputfile = outputfile
        self.public = public
        self.index = index

class TestGroup(object):
    def __init__(self, cases=None, points=None):
        self.cases = cases or []
        self.points = points
        self.threshold = 1.0

def find_test_files(test_dir, regexp):
    test_files = []
    r = re.compile(regexp)
    get_output = get_config_value('OUTPUT_FILENAME')
    for fn in os.listdir(test_dir):
        path = os.path.join(test_dir, fn)
        if not r.match(fn):
            continue
        opath = get_output(path)
        if not os.path.exists(opath):
            continue
        test_files.append((path, opath))
    return test_files

def collect_tests():
    defs = get_test_case_defs()
    gstore = defaultdict(TestGroup)
    test_cases = []
    for dirpath, regexp, parse in defs:
        test_files = find_test_files(dirpath, regexp)
        for ipath, opath in test_files:
            ret = parse(ipath)
            if ret is not None:
                case, public, groups = ret
                test_cases.append((case, groups, TestCase(ipath, opath, public)))
    assert len(test_cases) > 0
    test_cases.sort()
    tests = []
    for i, (case, grps, test) in enumerate(test_cases):
        test.index = i
        tests.append(test)
        for group in grps:
            g = gstore[group]
            g.cases.append(i)
    gkeys = list(gstore.keys())
    gkeys.sort()
    print(gkeys)
    groups = []
    for group in gkeys:
        g = gstore[group]
        g.cases.sort()
        groups.append(g)
    return tests, groups


def get_test_cases():
    test_cases, groups = collect_tests()
    total_points = get_config_value('TOTAL_POINTS')
    points = get_config_value('POINTS',
                    {'total':total_points, 'n':len(groups)})
    thresholds = get_config_value('THRESHOLDS', {'n':len(groups)})
    assert len(points) == len(groups)
    if total_points is not None:
        assert sum(points) == total_points
    if thresholds is not None:
        assert len(thresholds) == len(groups)
    else:
        thresholds = [1.0] * len(groups)
    for g, p, t in zip(groups, points, thresholds):
        g.points = p
        g.threshold = t
    return test_cases, groups

cases, groups = get_test_cases()


def create_dirs():
    for d in ('input', 'output', 'statement', 'gen', 'sol', 'check', 'att'):
        mkdir(d)


def copy_test_files():
    for c in cases:
        copy(c.inputfile, 'input/input{}.txt'.format(c.index))
        copy(c.outputfile, 'output/output{}.txt'.format(c.index))
    os.system('flip -u input/* output/*')


def copy_task():
    languages = get_config_value('STATEMENT_LANGUAGES', default=[])
    if languages:
        found = []
        for lang in languages:
            src = get_config_value('TASK_DESCRIPTION', {'language': lang})
            if os.path.isfile(src):
                copy(src, 'statement/statement-{}.pdf'.format(lang))
                found.append(lang)
        return found
    else:
        src = get_config_value('TASK_DESCRIPTION', {'language': ''})
        copy(src, 'statement/statement.pdf')


def write_scores():
    with open('gen/shared', 'w') as f:
        for g in groups:
            print('ST: {} {}'.format(g.points, g.threshold), file=f)
            for i in g.cases:
                print('{}  # {}'.format(i, os.path.relpath(cases[i].inputfile, test_dir)), file=f)


def copy_api():
    api_dir = get_config_value('API_DIR')
    api_private = get_config_value('API_DIR_PRIVATE', default=os.path.join(api_dir, 'private'))
    api_public = get_config_value('API_DIR_PUBLIC', default=os.path.join(api_dir, 'public'))
    os.system('rm -r sol/* att/*')
    if os.path.isdir(api_private):
        for fn in os.listdir(api_private):
            if fn.startswith('.'):
                continue
            copy(os.path.join(api_private, fn), os.path.join('sol', fn))
    if os.path.isdir(api_public):
        create_arc(api_public, 'att/{}.tgz'.format(task_name), type='tgz')

statement_languages = None

def write_yaml():
    data = OrderedDict()
    data['name'] = task_name
    data['title'] = get_config_value('TITLE') or task_name.capitalize()
    data['n_input'] = len(cases)
    data['public_testcases'] = ','.join(str(c.index) for c in cases if c.public)
    data['time_limit'] = get_config_value('TIME_LIMIT')
    data['memory_limit'] = get_config_value('MEMORY_LIMIT')
    data['infile'] = get_config_value('INPUT_FILE', default='')
    data['outfile'] = get_config_value('OUTPUT_FILE', default='')
    if statement_languages is not None:
        data['statement_languages'] = statement_languages
    data['primary_language'] = get_config_value('PRIMARY_STATEMENT', default='en')
    for k, v in get_config_value('PROPERTIES', default={}).items():
        data[k] = v
    with open('task.yaml', 'w') as f:
        #yaml.dump(data, f, default_flow_style=False)
        for k, v in data.items():
            yaml.dump({k: v}, f, default_flow_style=False)



def run():
    global statement_languages
    create_dirs()
    copy_test_files()
    statement_languages = copy_task()
    write_scores()
    copy_api()
    write_yaml()
    # TODO: checkers


run()

for cmd_f in get_config_value('RUN_COMMANDS', default=[]):
    cmd = get_value(cmd_f)
    print('run', cmd)
    os.system(cmd)


