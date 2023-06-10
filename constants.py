import enum

PORT = 4320
SERVER_START_KEYWORD = "start"


# raises ValueError if message types share a duplicate value
@enum.unique
class Msg(enum.IntEnum):
    """Enum for message types."""

    START = enum.auto()
    DEBUG = enum.auto()
