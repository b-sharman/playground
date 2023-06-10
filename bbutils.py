""" Shared code between client and server. """

from collections.abc import Callable
from typing import Any, NewType

import constants

Message = NewType("Message", dict)

def is_message_valid(message: Message) -> None:
    """ Raise ValueError if message does not meet protocol. """
    # must be a dict
    if type(message) != dict:
        raise ValueError("message is not a dict")

    # must have type
    if "type" not in message:
        raise ValueError("message has no type")

    # type must be specified in constants.Msg
    if message["type"] not in [tp for tp in constants.Msg]:
        raise ValueError("invalid message type")

def check_message_valid(func: Callable) -> Callable:
    """
    Decorator for any function that assumes message validity.

    The function must have the message as its first argument.
    """
    def checker(message: Message, *args, **kwargs) -> Callable[[Message], Any]:
        # will raise ValueError if message is not valid
        is_message_valid(message)
        return func(message, *args, **kwargs)
    return checker
