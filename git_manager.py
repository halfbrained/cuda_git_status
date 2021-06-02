import sys
import os
import re
import subprocess


class GitManager:
    def __init__(self):
        self.git = 'git'
        self.prefix = ''

    def run_git(self, cmd, cwd=None):
        plat = sys.platform
        if not cwd:
            cwd = self.getcwd()
        if cwd:
            if type(cmd) == str:
                cmd = [cmd]
            cmd = [self.git] + cmd
            if plat == "win32":
                # make sure console does not come up
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     cwd=cwd, startupinfo=startupinfo)
            else:
                my_env = os.environ.copy()
                my_env["PATH"] = "/usr/local/bin:/usr/bin:" + my_env["PATH"]
                p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     cwd=cwd, env=my_env)
            #p.wait()
            while p.poll() is None:
                yield None
            stdoutdata, _ = p.communicate()
            yield stdoutdata.decode('utf-8')

    def getcwd(self):
        f = self.filename
        cwd = None
        if f:
            cwd = os.path.dirname(f)
        return cwd

    def branch(self):
        for ret in self.run_git(["symbolic-ref", "HEAD", "--short"]): # wait for result
            if ret is None:
                yield None

        if ret:
            ret = ret.strip()
        else:
            for output in self.run_git("branch"): # wait for result
                if output is None:
                    yield None

            if output:
                m = re.search(r"\* *\(detached from (.*?)\)", output, flags=re.MULTILINE)
                if m:
                    ret = m.group(1)
        yield ret

    def is_dirty(self):
        for output in self.run_git("status"): # wait for result
            if output is None:
                yield None

        if not output:
            yield False
        ret = re.search(r"working (tree|directory) clean", output)
        if ret:
            yield False
        else:
            yield True

    def unpushed_info(self, branch):
        a, b = 0, 0
        if branch:
            for output in self.run_git(["branch", "-v"]): # wait for result
                if output is None:
                    yield None

            if output:
                m = re.search(r"\* .*?\[behind ([0-9])+\]", output, flags=re.MULTILINE)
                if m:
                    a = int(m.group(1))
                m = re.search(r"\* .*?\[ahead ([0-9])+\]", output, flags=re.MULTILINE)
                if m:
                    b = int(m.group(1))
        yield (a, b)

    def badge(self, filename):
        """ "coroutine" - call next() with result until received not None
        """

        self.filename = filename
        if not self.filename:
            yield ""

        branch = None
        for branch in self.branch(): # wait for result
            if branch is None:
                yield None

        if not branch:
            yield ""

        ret = branch
        for is_dirty in self.is_dirty(): # wait for result
            if is_dirty is None:
                yield None

        if is_dirty:
            ret = ret + "*"

        for unpushed_info in self.unpushed_info(branch): # wait for result
            if unpushed_info is None:
                yield None

        a, b = unpushed_info
        if a:
            ret = ret + "-%d" % a
        if b:
            ret = ret + "+%d" % b

        yield self.prefix + ret

