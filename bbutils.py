""" Shared code between client and server. """

from collections.abc import Callable
from typing import Any, NewType

import constants

Message = NewType("Message", dict)


def is_message_valid(message: Message) -> None:
    """Raise ValueError if message does not meet protocol."""
    # TODO: This is already hard to read and will only become more difficult. It might
    # be worthwhile to consider an external data validation library like cerberus.

    # must be a dict
    if type(message) != dict:
        raise ValueError("message is not a dict")

    # must have type
    if "type" not in message:
        raise ValueError("message has no type")

    # type must be specified in constants.Msg
    if message["type"] not in iter(constants.Msg):
        raise ValueError("invalid message type")

    # ids must be ints
    if "id" in message and not isinstance(message["id"], int):
        raise ValueError("client id is not int")

    # rq must be specified in constants.Rq
    if "rq" in message and message["rq"] not in iter(constants.Rq):
        raise ValueError("invalid message rq")

    # REQUEST must have rq
    if message["type"] == constants.Msg.REQUEST and "rq" not in message:
        raise ValueError("REQUEST message does not have rq")

    if message["type"] == constants.Msg.APPROVE:
        # APPROVE must have id
        if "id" not in message:
            raise ValueError("APPROVE message does not have id")
        # APPROVE must have rq
        if "rq" not in message:
            raise ValueError("APPROVE message does not have rq")


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
