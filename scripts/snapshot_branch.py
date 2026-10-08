"""Read/write ONLY snapshot.json on the data branch without altering the checkout."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def git(*args, input=None, env=None):
    return subprocess.run(['git',*args],input=input,text=True,capture_output=True,check=True,env=env).stdout.strip()


def main():
    action,path=sys.argv[1:]
    file=Path(path)
    exists=bool(git('ls-remote','--heads','origin','data'))
    parent=None
    if exists:
        git('fetch','origin','data')
        parent=git('rev-parse','FETCH_HEAD')
    if action=='restore':
        if parent:
            text=git('show',f'{parent}:snapshot.json')
            json.loads(text)
            file.parent.mkdir(parents=True,exist_ok=True)
            file.write_text(text+'\n')
        return
    if action!='save':raise ValueError('Use restore or save')
    json.loads(file.read_text())
    with tempfile.TemporaryDirectory() as directory:
        env={**os.environ,'GIT_INDEX_FILE':str(Path(directory)/'index'),
             'GIT_AUTHOR_NAME':'github-actions[bot]','GIT_AUTHOR_EMAIL':'41898282+github-actions[bot]@users.noreply.github.com',
             'GIT_COMMITTER_NAME':'github-actions[bot]','GIT_COMMITTER_EMAIL':'41898282+github-actions[bot]@users.noreply.github.com'}
        git('read-tree','--empty',env=env)
        blob=git('hash-object','-w',str(file))
        git('update-index','--add','--cacheinfo',f'100644,{blob},snapshot.json',env=env)
        tree=git('write-tree',env=env)
        if parent and git('rev-parse',f'{parent}^{{tree}}')==tree:return
        args=['commit-tree',tree]
        if parent:args+=['-p',parent]
        commit=git(*args,input='Update job skill snapshot\n',env=env)
        git('push','origin',f'{commit}:refs/heads/data')


if __name__=='__main__':main()
