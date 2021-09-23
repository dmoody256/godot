import os
import subprocess
import json
import concurrent.futures
import traceback
import sys
import time
import shlex
from git import Repo
from pkg_resources import parse_version
from timeit import default_timer as timer
import SCons
from SCons.Script import *

iwyu_bin = None
iwyu_tool = None
fix_include_bin = None
jobs_instance = None
iwyu_version = None
iwyu_python = sys.executable


def exists(env):
    global iwyu_bin, fix_include_bin, iwyu_tool, iwyu_version, iwyu_python

    iwyu_bin = env.WhereIs("include-what-you-use")
    if not iwyu_bin:
        iwyu_bin = env.WhereIs("include-what-you-use", os.environ["PATH"])
    if not iwyu_bin:
        iwyu_bin = env.WhereIs("iwyu")
        if not iwyu_bin:
            iwyu_bin = env.WhereIs("iwyu", os.environ["PATH"])

    iwyu_tool = env.WhereIs("iwyu_tool")
    if not iwyu_tool:
        iwyu_tool = env.WhereIs("iwyu_tool", os.environ["PATH"])

    fix_include_bin = env.WhereIs("fix_include")
    if not fix_include_bin:
        fix_include_bin = env.WhereIs("fix_include", os.environ["PATH"])

    if iwyu_bin:
        iwyu_version = parse_version(subprocess.getoutput(iwyu_bin + " --version").split()[1])
        if iwyu_version <= parse_version("0.9"):
            iwyu_python = "python2"

    return iwyu_bin and iwyu_tool and fix_include_bin


# ripped from https://stackoverflow.com/a/34325723/1644736
# Print iterations progress
def printProgressBar(iteration, total, prefix="", suffix="", decimals=1, length=100, fill="█", printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + "-" * (length - filledLength)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


def run_full_iwyu(env, target, source):

    current_procs = []
    max_procs = 6
    count = 0
    dot_time = 0

    start = timer()
    dot_time = start

    # with open(source[0].path) as f:
    #     compile_commands = json.load(f)

    #     l = len(compile_commands)
    #     files = set(
    #         [item["file"] for item in compile_commands if "clang" in os.path.basename(item["command"].split()[0])]
    #     )
    #     command_args = set(
    #         [item["command"][item["command"].find('clang'):].split()[1:] for item in compile_commands if "clang" in os.path.basename(shlex.split(item["command"])[0])]
    #     )
    #     l = len(command_args)
    #     printProgressBar(0, l, prefix="Progress:", suffix="Complete", length=50)
    #     with open(".iwyu.out", "w") as f:
    #         for index, command in enumerate(command_args):
    #             output = ""
    #             p = subprocess.Popen(
    #                 ['/home/ubuntu/include-what-you-use/build/bin/include-what-you-use'] + shlex.split(command), stdout=f, cwd=env.Dir("#").abspath
    #             )
    #             while p.poll() == None:
    #                 printProgressBar(index, l, prefix="Processing includes", suffix="Complete", length=50)
    #                 if jobs_instance.were_interrupted():
    #                     p.kill()

    #     with open(".iwyu.out") as f:
    #         p = subprocess.Popen([iwyu_python, fix_include_bin], stdin=f)
    #         while p.poll() == None:
    #             end = timer()
    #             if end - dot_time > 0.5:
    #                 count += 1
    #                 dot_time = end

    #             print(
    #                 "\r["
    #                 + "{:.2f}".format(round(end - start, 2))
    #                 + "] Fixing includes"
    #                 + "." * count
    #                 + " " * (6 - count),
    #                 end="\r",
    #             )

    #             if count > 5:
    #                 count = 0
    #             time.sleep(0.09)
    #             if jobs_instance.were_interrupted():
    #                 p.kill()

    def run_proc_thread(command):

        try:
            stdout, stderr = subprocess.Popen(['/home/ubuntu/include-what-you-use/build/bin/include-what-you-use'] + list(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=env.Dir('#').abspath).communicate()
            subprocess.Popen([sys.executable, '/home/ubuntu/include-what-you-use/fix_includes.py'], stdout=subprocess.PIPE, stdin=subprocess.PIPE).communicate(stderr)
        except:
            traceback.print_exc()

    with open(source[0].path) as f:
        compile_commands = json.load(f)

        command_args = set()
        for item in compile_commands:

            if "clang" in os.path.basename(shlex.split(item["command"])[0]):
                #print(item["command"].find('clang'):].split()[1:])
                com_arg_list = shlex.split(item["command"][item["command"].find('clang'):])[1:]
                command_tup = tuple(com_arg_list[:-1] + ['-I/usr/lib/llvm-7/lib/clang/7.0.0/include'] + com_arg_list[-1:])
                command_args.add(command_tup)
        # command_args = set(
        #     [item["command"][item["command"].find('clang'):].split()[1:] for item in compile_commands if "clang" in os.path.basename(shlex.split(item["command"])[0])]
        # )
        l = len(command_args)
        print(f"Files to process: {l}")
        # Initial call to print 0% progress
        printProgressBar(0, l, prefix = 'Progress:', suffix = 'Complete', length = 50)
        # We can use a with statement to ensure threads are cleaned up promptly
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Start the load operations and mark each future with its URL
            futures = {executor.submit(run_proc_thread, item): item for item in command_args}
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                future.result()
                if jobs_instance.were_interrupted():
                    executor._threads.clear()
                    concurrent.futures.thread._threads_queues.clear()
                    break
                printProgressBar(i + 1, l, prefix = 'Progress:', suffix = 'Complete', length = 50)


def run_changeset_iwyu(env, target, source):
    with open(".iwyu.out", "w") as f:
        output = ""
        p = subprocess.Popen(
            [iwyu_python, iwyu_tool, "-p", "compile_commands.json"]
            + [s.path for s in source if s.path != "compile_commands.json"],
            stdout=f,
            cwd=env.Dir("#").abspath,
        )
        p.communicate()

    with open(".iwyu.out") as f:
        p = subprocess.Popen([iwyu_python, fix_include_bin, "--nosafe_headers", "--comments"], stdin=subprocess.PIPE)
        p.communicate(f.read().encode("utf-8"))


def generate(env):
    global jobs_instance
    # if not iwyu_bin or fix_include_bin:
    #     if not exists(env):
    #         return

    if "run-iwyu" in COMMAND_LINE_TARGETS:

        # for target in COMMAND_LINE_TARGETS:
        #     if target == "run-iwyu":
        #         continue
        #     env.Depends(target, "run-iwyu")

        # scons does not expose this interface so we hack our
        # way in so we can interrupt the potentially long
        # execution of the run-iwyu task.
        original_jobs_init = SCons.Job.Jobs.__init__

        def jobs_instance_stealer(self, num, taskmaster):
            global jobs_instance
            jobs_instance = self
            return original_jobs_init(self, num, taskmaster)

        SCons.Job.Jobs.__init__ = jobs_instance_stealer

        run_iwyu = env.Command(target="run-iwyu-target", source="compile_commands.json", action=run_full_iwyu)
        env.AlwaysBuild(run_iwyu)
        env.Alias("run-iwyu", run_iwyu)

    # repo = Repo(env.Dir("#").abspath)

    # # Cribbed from Tool/cc.py and Tool/c++.py. It would be better if
    # # we could obtain this from SCons.
    # _CSuffixes = [".c"]
    # if not SCons.Util.case_sensitive_suffixes(".c", ".C"):
    #     _CSuffixes.append(".C")

    # _CXXSuffixes = [".cpp", ".cc", ".cxx", ".c++", ".C++"]
    # if SCons.Util.case_sensitive_suffixes(".c", ".C"):
    #     _CXXSuffixes.append(".C")
    # files = [
    #     item.a_path for item in repo.index.diff(None) if os.path.splitext(item.a_path)[1] in _CXXSuffixes + _CSuffixes
    # ]
    # print(files)
    # if files and "run-iwyu" not in COMMAND_LINE_TARGETS:
    #     changeset_iwyu = env.Command(
    #         target=".iwyu.out", source=["compile_commands.json"] + files, action=run_changeset_iwyu
    #     )
    #     Default(changeset_iwyu)
    #     for target in COMMAND_LINE_TARGETS:
    #         if target == ".iwyu.out":
    #             continue
    #         if target == "compile_commands.json":
    #             continue
    #         #env.Alias(str(target), changeset_iwyu)
    #         env.Depends(target, changeset_iwyu)

