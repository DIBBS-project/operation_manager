from __future__ import print_function

import os
import errno
import shutil
from six.moves import urllib

from invoke import task
from invoke.exceptions import Exit

ROOT = os.path.abspath(os.path.dirname(__file__))
PACKAGE_NAME = 'tbd'


def fileurl(path):
    path = os.path.abspath(path)
    return urllib.parse.urljoin('file:', urllib.request.pathname2url(path))


@task
def test(ctx, coverage=False, verbose=False):
    runner = "coverage run" if coverage else "python"
    args = "manage.py test {}".format('--verbosity 2' if verbose else '')

    result = ctx.run('{} {}'.format(runner, args), warn=True)

    if coverage:
        ctx.run('coverage xml')
        ctx.run('coverage html')
        ctx.run('coverage report')

    if not result.ok:
        # delay failed test return so we can make reports first
        raise Exit(result.exited)


@task
def report(ctx):
    import webbrowser
    webbrowser.open_new_tab(fileurl(os.path.join(ROOT, 'coverage_html_report', 'index.html')))
