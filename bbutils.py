""" Shared code between client and server. """

import typing

import constants

def is_message_valid(message: dict):
    """ Raise ValueError if message does not meet protocol. """

    if type(message) != dict:
        raise ValueError("message is not a dict")

    # must have type
    if "type" not in message:
        raise ValueError("message has no type")

    # type must be specified in constants.Msg
    if message["type"] not in [tp for tp in constants.Msg]:
        raise ValueError("invalid message type")

def check_message_valid(func: typing.Callable) -> typing.Callable:
    """
    Decorator for any function that assumes message validity.

    The function must have the message as its first argument.
    """
    def checker(message: dict, *args, **kwargs):
        # will raise ValueError if message is not valid
        is_message_valid(message)
        return func(message, *args, **kwargs)
    return checker
