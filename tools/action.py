"""
Common action registry for JARVIS tools.
"""

from functools import wraps

_ACTIONS = {}


def action(name: str):
    """
    Register a function as a JARVIS tool action.
    """

    def decorator(func):

        _ACTIONS[name] = func

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_action(name: str):
    return _ACTIONS.get(name)


def list_actions():
    return sorted(_ACTIONS.keys())
