""" Shared code between client and server. """

from collections.abc import Callable
import json
from typing import Any, NewType
import websockets.client
import websockets.server

import constants
import socket

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

    # id must be int
    if "id" in message and not isinstance(message["id"], int):
        raise ValueError("client id is not int")

    # name must be str
    if "name" in message and not isinstance(message["name"], str):
        raise ValueError("client name is not str")

    # rq must be specified in constants.Rq
    if "rq" in message and message["rq"] not in iter(constants.Rq):
        raise ValueError("invalid message rq")

    # type-specific requirements
    match message["type"]:
        case constants.Msg.APPROVE:
            # APPROVE must have id
            if "id" not in message:
                raise ValueError("APPROVE message does not have id")
            # APPROVE must have state
            if "state" not in message:
                raise ValueError("APPROVE message does not have state")

        # ID must have id
        case constants.Msg.ID if "id" not in message:
            raise ValueError("ID message does not have id")

        # GREET must have name
        case constants.Msg.GREET if "name" not in message:
            raise ValueError("GREET message does not have name")

        # REQUEST must have rq
        case constants.Msg.REQUEST if "rq" not in message:
            raise ValueError("REQUEST message does not have rq")


def get_local_ip():
    """Return the computer's local IP address."""
    # based on https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        # The following raises socket.error if not connected to Internet
        # Wrote a simple try-except to get around.
        try:
            s.connect(("8.8.8.8", 80))
        except (socket.error, OSError):
            raise RuntimeError(
                "Connection didn't work; are you connected to the internet?"
            )
        else:
            return s.getsockname()[0]


class _BBSharedProtocol:
    """WebSocketClientProtocol with send() that enforces JSON format."""

    async def send(self, message: Message) -> None:
        """
        Serialize message to json and call the regular send on it.

        This method also enforces message validity; it is decorated by
        check_message_valid.
        """
        is_message_valid(message)
        await super().send(json.dumps(message))


class BBClientProtocol(_BBSharedProtocol, websockets.client.WebSocketClientProtocol):
    pass


class BBServerProtocol(_BBSharedProtocol, websockets.server.WebSocketServerProtocol):
    pass
