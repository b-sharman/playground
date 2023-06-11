import enum

PORT = 4320
SERVER_START_KEYWORD = "start"


# raises ValueError if message types share a duplicate value
@enum.unique
class Msg(enum.IntEnum):
    """Enum for message types."""

    START = enum.auto()    # game starts
    REQUEST = enum.auto()  # client requests server to move, shoot, etc.
    APPROVE = enum.auto()  # server broadcasts approval to a REQUEST


@enum.unique
class Rq(enum.IntEnum):
    """
    Enum for request types.

    A request is a message sent by a player asking to move, shoot, etc.
    """

    UP = enum.auto()
    DOWN = enum.auto()
    SHOOT = enum.auto()
