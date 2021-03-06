# Copyright (C) 2009, Hyves (Startphone Ltd.)
#
# This module is part of the Concurrence Framework and is released under
# the New BSD License: http://www.opensource.org/licenses/bsd-license.php

import time

from concurrence import Tasklet, TaskLocal, TIMEOUT_NEVER, TIMEOUT_CURRENT

class _Timeout(object):
    def __init__(self):
        self._timeout_stack = [Tasklet.current()._timeout_time]

    def push(self, timeout):
        current_timeout = self._timeout_stack[-1]
        assert current_timeout != TIMEOUT_CURRENT
        if timeout == TIMEOUT_CURRENT:
            self._timeout_stack.append(current_timeout)
        elif timeout == TIMEOUT_NEVER and current_timeout == TIMEOUT_NEVER:
            self._timeout_stack.append(timeout)
        elif timeout == TIMEOUT_NEVER and current_timeout != TIMEOUT_NEVER:
            self._timeout_stack.append(current_timeout)
        else:
            _timeout_time = time.time() + timeout
            if current_timeout == TIMEOUT_NEVER:
                self._timeout_stack.append(_timeout_time)
            else:
                self._timeout_stack.append(min(_timeout_time, current_timeout))

        Tasklet.current()._timeout_time = self._timeout_stack[-1]

    def pop(self):
        assert len(self._timeout_stack) > 1, "unmatched pop, did you forget to push?"
        self._timeout_stack.pop()
        Tasklet.current()._timeout_time = self._timeout_stack[-1]
        return len(self._timeout_stack) > 1

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        Timeout.pop()


class Timeout:
    """Task based timeout. The :class:`Timeout` class lets you set a timeout for the current task.
    If the task takes longer than *timeout* seconds after the timeout is set, a :class:`~concurrence.core.TimeoutError` is raised
    inside the task.

    Timeouts form a stack and you can always :func:`push` a new timeout on top of the current one. Every :func:`push` must be matched
    by a corresponding call to :func:`pop`. As a convenience you can use pythons `with` statement to do the pop automatically.

    Timeout example::

        with Timeout.push(30):  #everything in following block must be finished within 30 seconds
            ...
            ...
            with Timeout.push(5):
                cnn = get_database_connection() #must return within 5 seconds
            ...
            ...

    """

    _local = TaskLocal()

    @classmethod
    def push(cls, timeout):
        """Pushes a new *timeout* in seconds for the current task."""
        try:
            t = cls._local.t
        except AttributeError:
            t = _Timeout()
            cls._local.t = t
        t.push(timeout)
        return t

    @classmethod
    def pop(cls):
        """Pops the current timeout for the current task."""
        try:
            t = cls._local.t
            if not t.pop():
                del cls._local.t
        except AttributeError:
            assert False, "no timeout was pushed for the current task"

    @classmethod
    def current(cls):
        """Gets the current timeout for the current task in seconds. That is the number of seconds before the current task
        will timeout by raising a :class:`~concurrence.core.TimeoutError`. A timeout of TIMEOUT_NEVER indicates that there is no timeout for the
        current task."""
        return Tasklet.get_current_timeout()

