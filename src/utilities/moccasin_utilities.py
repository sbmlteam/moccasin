# Library of random utilities.

import sys, functools, inspect

# Extremely helpful debugging aid posted by Florian Brucker posted to
# http://stackoverflow.com/a/24743279/743730
#
# Usage example:
#   @parse_debug_helper
#   def some_parse_action(tokens):
#       ....
#
# where "some_parse_action" is a method you attach via setParseAction(...) to
# some part of your pyparsing grammar.
#
def parse_debug_helper(f):
    """
    Decorator for pyparsing parse actions to ease debugging.

    pyparsing uses trial & error to deduce the number of arguments a parse
    action accepts. Unfortunately any ``TypeError`` raised by a parse action
    confuses that mechanism.

    This decorator replaces the trial & error mechanism with one based on
    reflection. If the decorated function itself raises a ``TypeError`` then
    that exception is re-raised if the wrapper is called with less arguments
    than required. This makes sure that the actual ``TypeError`` bubbles up
    from the call to the parse action (instead of the one caused by pyparsing's
    trial & error).
    """
    num_args = len(inspect.getargspec(f).args)
    if num_args > 3:
        raise ValueError('Input function must take no more than 3 parameters.')

    @functools.wraps(f)
    def action(*args):
        if len(args) < num_args:
            if action.exc_info:
                raise action.exc_info[0], action.exc_info[1], action.exc_info[2]
        action.exc_info = None
        try:
            return f(*args[:-(num_args + 1):-1])
        except TypeError as e:
            action.exc_info = sys.exc_info()
            raise

    action.exc = None
    return action
