from __future__ import print_function

import os
import errno
import shutil
from six.moves import urllib

from invoke import task

ROOT = os.path.abspath(os.path.dirname(__file__))
PACKAGE_NAME = 'tbd'


def fileurl(path):
    path = os.path.abspath(path)
    return urllib.parse.urljoin('file:', urllib.request.pathname2url(path))


@task
def clean(ctx):
    rm_targets = ['build', 'dist', '{}.egg-info'.format(PACKAGE_NAME)]


@task
def test(ctx, coverage=False):
    if coverage:
        cmd = "coverage run manage.py test"
    else:
        cmd = 'python manage.py test'

    ctx.run(cmd)

    if coverage:
        ctx.run('coverage xml')
        ctx.run('coverage html')


@task
def report(ctx):
    import webbrowser
    webbrowser.open_new_tab(fileurl(os.path.join(ROOT, 'coverage_html_report', 'index.html')))
