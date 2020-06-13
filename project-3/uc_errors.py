from contextlib import contextmanager

###########################################################
## uC Error Handling Helper ###############################
###########################################################

_subscribers = []
_num_errors = 0

def error(lineno, message, filename=None):
    ''' Report a compiler error to all subscribers. '''
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
    ''' Return the number of errors reported. '''
    return _num_errors

def clear_errors():
    ''' Reset the total number of errors reported to 0. '''
    global _num_errors
    _num_errors = 0

@contextmanager
def subscribe_errors(handler):
    ''' Context manager that allows monitoring of compiler error messages.\n
        Use as follows, where `handler` is a callable taking a single argument which is the error message string:
        ```
        with subscribe_errors(handler):
            # ... do compiler ops ...
        ```
    '''
    _subscribers.append(handler)
    try:
        yield
    finally:
        _subscribers.remove(handler)