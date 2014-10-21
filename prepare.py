#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys, os, re, shutil, yaml
from collections import defaultdict, OrderedDict
from zipfile import ZipFile

assert __name__ == '__main__'

if len(sys.argv) > 1:
    os.chdir(sys.argv[1])
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

import config

def copy(src, dst):
    print 'copy', src, '->', dst
    shutil.copyfile(src, dst)

def create_zip(dir, zipfile):
    with ZipFile(zipfile, 'w') as z:
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
                print 'zip', path, '->', '{}:{}'.format(zipfile, rpath)
                z.write(path, rpath)

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

home_dir = get_config_value('HOME_DIR', default='/home/lioadmin/.prep/')
home_join = lambda *path: os.path.join(home_dir, *path)
test_dir = get_config_value('TEST_DIR', {'taskname':task_name})


def get_test_case_defs():
    defs = get_config_value('TESTS')
    defs = [(get_value(prefix, {'taskname':task_name}), filter, public) for prefix, filter, public in defs]
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

input_re = re.compile(get_config_value('INPUT_SUFFIX'))
output_re = re.compile(get_config_value('OUTPUT_SUFFIX'))

def find_test_files(prefix):
    inputs = {}
    outputs = {}
    for fn in os.listdir(test_dir):
        path = os.path.join(test_dir, fn)
        if not fn.startswith(prefix):
            continue
        suffix = fn[len(prefix):]
        for regex, store in [(input_re, inputs), (output_re, outputs)]:
            m = regex.match(suffix)
            if not m:
                continue
            group = m.group('testgroup')
            try:
                case = m.group('testcase')
            except IndexError:
                case = None
            store[group, case] = path
    return inputs, outputs

def collect_tests():
    defs = get_test_case_defs()
    gstore = defaultdict(TestGroup)
    for prefix, filter_f, public_f in defs:
        inputs, outputs = find_test_files(prefix)
        cases = list(sorted(set(inputs.keys() + outputs.keys())))
        for group, case in cases:
            context = {'testgroup': group, 'testcase': case}
            inc = get_value(filter_f, context)
            if not inc:
                continue
            assert group, case in inputs
            assert group, case in outputs
            public = get_value(public_f, context)
            g = gstore[group]
            c = TestCase(inputs[group, case], outputs[group, case], public)
            g.cases.append(c)
    groups = []
    for group in sorted(gstore.keys()):
        groups.append(gstore[group])
    return groups


def get_test_cases():
    groups = collect_tests()
    total_points = get_config_value('TOTAL_POINTS')
    points = get_config_value('POINTS',
                    {'total':total_points, 'n':len(groups)})
    assert len(points) == len(groups)
    if total_points is not None:
        assert sum(points) == total_points
    idx = 0
    for g, p in zip(groups, points):
        g.points = p
        for c in g.cases:
            c.index = idx
            idx += 1
    return groups

tests = get_test_cases()


def create_dirs():
    for d in ('input', 'output', 'statement', 'gen', 'sol', 'check', 'att'):
        mkdir(d)


def copy_test_files():
    for g in tests:
        for c in g.cases:
            copy(c.inputfile, 'input/input{}.txt'.format(c.index))
            copy(c.outputfile, 'output/output{}.txt'.format(c.index))
    os.system('flip -u input/* output/*')


def copy_task():
    src = get_config_value('TASK_DESCRIPTION', {'taskname':task_name})
    copy(src, 'statement/statement.pdf')


def write_scores():
    with open('gen/GEN', 'w') as f:
        for g in tests:
            print >> f, '# ST: {}'.format(g.points)
            for c in g.cases:
                print >> f, os.path.basename(c.inputfile)


def copy_api():
    api_dir = get_config_value('API_DIR', {'taskname': task_name})
    api_private = os.path.join(api_dir, 'private')
    api_public = os.path.join(api_dir, 'public')
    os.system('rm -r sol/* att/*')
    if os.path.isdir(api_private):
        for fn in os.listdir(api_private):
            if fn.startswith('.'):
                continue
            copy(os.path.join(api_private, fn), os.path.join('sol', fn))
    if os.path.isdir(api_public):
        create_zip(api_public, 'att/{}.zip'.format(task_name))


def write_yaml():
    data = OrderedDict()
    data['name'] = task_name
    data['title'] = get_config_value('TITLE', default=task_name)
    data['n_input'] = sum(len(g.cases) for g in tests)
    data['public_testcases'] = ','.join(str(c.index) for g in tests for c in g.cases if c.public)
    data['time_limit'] = get_config_value('TIME_LIMIT')
    data['memory_limit'] = get_config_value('MEMORY_LIMIT')
    data['infile'] = get_config_value('INPUT_FILE', {'taskname': task_name}, default='')
    data['outfile'] = get_config_value('OUTPUT_FILE', {'taskname': task_name}, default='')
    data['primary_language'] = get_config_value('PRIMARY_STATEMENT', default='lt')
    for k, v in get_config_value('PROPERTIES', default={}).iteritems():
        data[k] = v
    with open('{}.yaml'.format(task_name), 'w') as f:
        #yaml.dump(data, f, default_flow_style=False)
        for k, v in data.iteritems():
            yaml.dump({k: v}, f, default_flow_style=False)



def run():
    create_dirs()
    copy_test_files()
    copy_task()
    write_scores()
    copy_api()
    write_yaml()
    # TODO: checkers


run()

for cmd_f in get_config_value('RUN_COMMANDS', default=[]):
    cmd = get_value(cmd_f, {'taskname':task_name})
    print 'run', cmd
    os.system(cmd)


