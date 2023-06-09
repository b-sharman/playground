import enum

PORT = 4320
SERVER_START_KEYWORD = "start"

# message types
@enum.unique # raises ValueError if message types share a duplicate ID
class Msg(enum.IntEnum):
    START = enum.auto()
    DEBUG = enum.auto()
