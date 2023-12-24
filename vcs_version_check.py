#!/usr/bin/env python3
# 2023.12 yudai.yamazaki

import subprocess
import re
import argparse
from pathlib import Path

import yaml

color_dic = {'r':'\033[31m', 'g':'\033[32m', 'b':'\033[34m', 'y':'\033[33m'}
def printc(text, color='w'):
    if color == 'w':
        print(text)
    else:
        print(color_dic[color] + text + '\033[0m')

def get_sha(src_dir):
    cmd = 'cd ' + src_dir + ' && git log -1 | grep commit'
    res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, executable='/bin/bash', shell=True)
    return res.stdout.strip().replace('commit ', '')

def get_branch(src_dir):
    cmd = 'cd ' + src_dir + ' && git branch'
    res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, executable='/bin/bash', shell=True)
    for branch in res.stdout.splitlines():
        if '*' in branch:
            return branch.replace('* ', '')

def get_uncommit(src_dir) -> int:
    cmd = 'cd ' + src_dir + ' && git status -s'
    res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, executable='/bin/bash', shell=True)
    l = res.stdout.splitlines()
    return len(l)

def get_ahead_behind(src_dir, no_fetch):
    if not no_fetch:
        cmd = 'cd ' + src_dir + ' && git fetch'
        subprocess.run(cmd, stdout=subprocess.PIPE, text=True, executable='/bin/bash', shell=True)
    cmd = 'cd ' + src_dir + ' && git branch -v'
    res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, executable='/bin/bash', shell=True)
    if '[' in res.stdout:
        ahead_behind = re.split(r'[\[\]]', res.stdout)[1]
        return ahead_behind
    else:
        return None

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('repos' , help='Reference .repos file')
    parser.add_argument('root_dir', help='Repositories root dir')
    parser.add_argument('--no_fetch' ,action='store_true', help='Disable to run git fetch')
    args = parser.parse_args()

    repos_file   = args.repos
    src_root_dir = args.root_dir

    correct = 0
    incorrect = 0
    diff_remote = 0
    uncommitted = 0
    with open(repos_file, mode='r') as s:
        repos:dict
        repos = yaml.safe_load(s)['repositories']
        for repo, desc in repos.items():
            src_dir = src_root_dir + '/' + repo
            version = desc['version']

            printc('=== ' + repo + ' ===', 'b')
            printc('version     : ' + version)

            if not Path(src_dir).exists():
                printc(src_dir + ' not found!', 'r')
                incorrect += 1
                continue

            local_sha = get_sha(src_dir)
            if version == local_sha:
                printc('local ver   : ' + local_sha)
                correct += 1
            else:
                local_branch = get_branch(src_dir)
                if version == local_branch:
                    printc('local ver   : ' + local_branch)
                    correct += 1

                    ahead_behind = get_ahead_behind(src_dir, args.no_fetch)
                    if ahead_behind:
                        printc('>> diff remote : ' + ahead_behind + ' commits', 'y')
                        diff_remote += 1
                else:
                    printc('>> local ver   : ' + local_branch, 'y')
                    incorrect += 1
            
            uncommit = get_uncommit(src_dir)
            if uncommit:
                printc('>> uncommitted : ' + str(uncommit) + ' files changed', 'y')
                uncommitted += 1
    
    print('===')
    sum = correct + incorrect
    if correct == sum:
        printc('All repositories correct versions.')
    else:
        printc(str(incorrect) + ' repositories incorrect versions!', 'y')

    if diff_remote:
        printc(str(diff_remote) + ' repositories different from remote!', 'y')

    if uncommitted:
        printc(str(uncommitted) + ' repositories have uncommitted change!', 'y')
