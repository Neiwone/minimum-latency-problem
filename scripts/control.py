"""
Keyboard control of a running batch: Ctrl+P pauses and resumes it, Ctrl+Q
stops it and shows the report over the runs done so far.

Solvers measure their own wall-clock time (--max-time, TIME_MS), so a run
cannot be frozen and continued: the pause would count as solver time. The
run in progress when either key is pressed is killed and not saved instead;
after a pause it is redone from scratch. Every saved run is therefore a run
that was never paused.

Only active when stdin is a terminal (not under nohup or a pipe).
"""
import os
import select
import sys
import threading
import time
from contextlib import contextmanager

try:
    import termios
    import tty
except ImportError:          # not a POSIX terminal: keys are just not available
    termios = None

CTRL_P = b"\x10"
CTRL_Q = b"\x11"


class BatchStopped(Exception):
    """Ctrl+Q: stop starting runs and report what is there."""


class RunInterrupted(Exception):
    """The run in progress was killed by Ctrl+P or Ctrl+Q; it is not saved."""


class Control:
    def __init__(self):
        self.stopped = False
        self.paused = False
        # Set while paused or stopped: a solver that is running gets killed.
        self.interrupt = threading.Event()
        self.paused_seconds = 0.0
        self._pause_start = None
        self._cond = threading.Condition()
        self._fd = None
        self._saved_attrs = None
        self._thread = None
        self._active = False
        # Set by run_experiments' status line while it is on screen, so these
        # messages do not land in the middle of it.
        self.printer = None

    # ---- used by the runner ----

    def wait_to_run(self):
        """Call before starting a run: blocks while paused, and raises
        BatchStopped once Ctrl+Q was pressed."""
        with self._cond:
            while self.paused and not self.stopped:
                self._cond.wait()
            if self.stopped:
                raise BatchStopped()

    # ---- keys ----

    def _say(self, msg):
        (self.printer or print)(f"[{msg}]", flush=True)

    def _end_pause(self):
        if self._pause_start is not None:
            self.paused_seconds += time.monotonic() - self._pause_start
            self._pause_start = None

    def _on_key(self, key):
        with self._cond:
            if self.stopped:
                return
            if key == CTRL_Q:
                self.stopped = True
                self.paused = False
                self._end_pause()
                self.interrupt.set()
                self._say("Ctrl+Q: stopping -- the run in progress is discarded; reporting the runs done so far")
            elif key == CTRL_P and not self.paused:
                self.paused = True
                self._pause_start = time.monotonic()
                self.interrupt.set()
                self._say("Ctrl+P: paused -- the run in progress is discarded and will be redone. Ctrl+P resumes, Ctrl+Q stops")
            elif key == CTRL_P:
                self.paused = False
                self._end_pause()
                self.interrupt.clear()
                self._say("Ctrl+P: resumed")
            self._cond.notify_all()

    def _listen(self):
        while self._active:
            ready, _, _ = select.select([self._fd], [], [], 0.1)
            if ready and self._active:
                self._on_key(os.read(self._fd, 1))

    def _start(self):
        if termios is None or not sys.stdin.isatty():
            return False
        self._fd = sys.stdin.fileno()
        self._saved_attrs = termios.tcgetattr(self._fd)
        tty.setcbreak(self._fd)
        # Ctrl+Q is XON to a terminal with flow control on; turn that off so
        # the key reaches us. Ctrl+C keeps working.
        attrs = termios.tcgetattr(self._fd)
        attrs[0] &= ~termios.IXON
        termios.tcsetattr(self._fd, termios.TCSADRAIN, attrs)
        self._active = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        return True

    def _stop(self):
        if not self._active:
            return
        self._active = False
        self._thread.join()
        termios.tcsetattr(self._fd, termios.TCSADRAIN, self._saved_attrs)

    @contextmanager
    def listening(self):
        """Listen for the keys for the duration of a batch; always gives the
        terminal back as it was."""
        if self._start():
            print("Ctrl+P pauses and resumes, Ctrl+Q stops and shows the report.",
                  flush=True)
        try:
            yield
        finally:
            self._stop()

    @contextmanager
    def suspended(self):
        """Hand the terminal back for an input() prompt."""
        was_active = self._active
        self._stop()
        try:
            yield
        finally:
            if was_active:
                self._start()


CONTROL = Control()
