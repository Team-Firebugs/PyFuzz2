__author__ = 'susperius'

import gevent
import os
import time
import psutil
import subprocess
import logging
from debugging.windbg import Debugger


class DebuggerWorker:
    def __init__(self, program_path, fuzzer, report_queue, sleep_time, dbg_child=False):
        self._logger = logging.getLogger(__name__)
        self._greenlet = None
        self._process = None
        self._running = False
        self._program_path = program_path
        self._testcase = ""
        self._crash_occurred = False
        self._crash_report = ""
        self._fuzzer = fuzzer
        self._report_queue = report_queue
        self._sleep_time = sleep_time
        self._dbg_child = dbg_child

    def __debugger_worker_green(self):
        while True:
            self.__create_testcases()
            for filename in os.listdir("testcases/"):
                output = ""
                testcase_dir = os.getcwd() + "\\testcases\\"
                if self._dbg_child:
                    process = subprocess.Popen(
                        "python debugging\\windbg.py -p \"" + self._program_path
                        + "\" -t \"" + testcase_dir + filename + "\"",
                        stdout=subprocess.PIPE)
                else:
                    process = subprocess.Popen(
                        "python debugging\\windbg.py -p \"" + self._program_path
                        + "\" -t \"" + testcase_dir + filename + "\" -c",
                        stdout=subprocess.PIPE)
                self._logger.debug("Debugger started...")
                util = psutil.Process(process.pid)
                start = time.time()
                try:
                    while True:
                        if time.time() - start > self._sleep_time:
                            break
                        elif util.cpu_percent(1.0) == 0.0:
                            break
                except:
                    pass # just ignore
                process.kill()
                output = process.stdout.read()
                if "Crash Report" in output:
                    with open(testcase_dir + filename, "rb") as fd:
                        testcase = fd.read()
                    self._report_queue.put((output, testcase))
                gevent.sleep(0)
                x -= 1

    def __create_testcases(self):
        for i in range(100):
            filename = "test" + str(i) if i > 9 else "test0" + str(i)
            filename += "." + self._fuzzer.file_type
            with open("testcases/" + filename, "wb+") as fd:
                fd.write(self._fuzzer.fuzz())


    def start_worker(self):
        if self._greenlet is None:
            self._greenlet = gevent.spawn(self.__debugger_worker_green)

    def stop_worker(self):
        if self._greenlet is not None:
            gevent.kill(self._greenlet)

