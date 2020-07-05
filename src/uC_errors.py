from contextlib import contextmanager

###########################################################
## uC Error Handling Helper ###############################
###########################################################

_subscribers = []
_num_errors = 0


def error(lineno, message, filename=None):
    """ Report a compiler error to all subscribers. """
    global _num_errors
    if not filename:
        if not lineno:
            errmsg = "{}".format(message)
        else:
            errmsg = "{}: {}".format(lineno, message)
    else:
        if not lineno:
            errmsg = "{}: {}".format(filename, message)
        else:
            errmsg = "{}:{}: {}".format(filename, lineno, message)
    for subscriber in _subscribers:
        subscriber(errmsg)
    _num_errors += 1


def errors_reported():
    """ Return the number of errors reported. """
    return _num_errors


def clear_errors():
    """ Reset the total number of errors reported to 0. """
    global _num_errors
    _num_errors = 0


@contextmanager
def subscribe_errors(handler):
    """ Context manager that allows monitoring of compiler error messages.\n
        Use as follows, where `handler` is a callable taking a single argument which is the error message string:
        ```
        with subscribe_errors(handler):
            # ... do compiler ops ...
        ```
    """
    _subscribers.append(handler)
    try:
        yield
    finally:
        _subscribers.remove(handler)


# NOTE The utility function `errors_reported()` returns the total number of errors reported so far.
#      Different stages of the compiler might use this to decide whether or not to keep processing or not.
#      Use `clear_errors()` to clear the total number of errors.

# NOTE Error handling is based on a subscription based model using context-managers and the `subscribe_errors()` function.
#
#      For example, to route error messages to standard output, use this:
#          with subscribe_errors(print):
#              run_compiler()
#
#      To send messages to standard error, you can do this:
#          from functools import partial
#          with subscribe_errors(partial(print, file=sys.stderr)):
#               run_compiler()
#
#      To route messages to a logger, you can do this:
#          import logging
#          log = logging.getLogger("somelogger")
#          with subscribe_errors(log.error):
#               run_compiler()
#
#      To collect error messages for the purpose of unit testing, do this:
#          errs = []
#          with subscribe_errors(errs.append):
#               run_compiler()
#          # Check errs for specific errors
