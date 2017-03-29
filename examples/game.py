import logging
import os.path
import input_helper as ih
import redis_helper as rh
from functools import partial
from enum import Enum


LOGFILE = os.path.abspath('log--mmorpg-game.log')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(LOGFILE, mode='a')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(funcName)s: %(message)s'
))
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
logger.addHandler(file_handler)
logger.addHandler(console_handler)


PLAYERS = rh.Collection(
    'mmo',
    'player',
    unique_field='handle',
    index_fields='email,status',
    insert_ts=True
)

CHARACTERS = rh.Collection(
    'mmo',
    'character',
    unique_field='name',
    index_fields='species,specialty,rank,player,status',
    insert_ts=True
)

ITEMS = rh.Collection(
    'mmo',
    'item',
    unique_field='name',
)

MESSAGES = rh.Collection(
    'mmo',
    'message',
    index_fields='to,from',
)


class character_status(Enum):
    full_health = 1
    medium_health = 2
    low_health = 3
    critical_health = 4
    dead = 5
    un_dead = 6


class Player(object):
    """A specific human that is playing the game"""
    def __init__(self, handle, **kwargs):
        self._collection = PLAYERS
        _handle = handle.replace(' ', '_').lower()


class CharacterController(object):
    """Controlls a particular character"""
    x_positions = 'mmo:positions:x'
    y_positions = 'mmo:positions:y'

    @classmethod
    def move_right(cls, character_name, n=1, log=True):
        """Move 'character_name' right 'n' spaces and log"""
        rh.REDIS.hincrbyfloat(cls.x_positions, character_name, n)
        if log:
            logger.info('Character {} moved right by {}'.format(character_name, n))

    @classmethod
    def move_left(cls, character_name, n=1, log=True):
        """Move 'character_name' left 'n' spaces and log"""
        rh.REDIS.hincrbyfloat(cls.x_positions, character_name, -1 * n)
        if log:
            logger.info('Character {} moved left by {}'.format(character_name, n))

    @classmethod
    def move_up(cls, character_name, n=1, log=True):
        """Move 'character_name' up 'n' spaces and log"""
        rh.REDIS.hincrbyfloat(cls.y_positions, character_name, n)
        if log:
            logger.info('Character {} moved up by {}'.format(character_name, n))

    @classmethod
    def move_down(cls, character_name, n=1, log=True):
        """Move 'character_name' down 'n' spaces and log"""
        rh.REDIS.hincrbyfloat(cls.y_positions, character_name, -1 * n)
        if log:
            logger.info('Character {} moved down by {}'.format(character_name, n))

    @classmethod
    def get_position(cls, character_name, log=True):
        """Log current position for character_name and return coordinates as a dict"""
        position = {
            'x': ih.decode(rh.REDIS.hget(cls.x_positions, character_name)) or 0,
            'y': ih.decode(rh.REDIS.hget(cls.y_positions, character_name)) or 0,
        }
        if log:
            logger.info('Character {} is at position ({}, {})'.format(
                character_name,
                position['x'],
                position['y']
            ))
        return position


try:
    from chloop import GetCharLoop
except ImportError:
    logger.error('Install "chloop" package to this virtual environment to run the gameloop')
    GameLoop = None
    gameloop = None
else:
    class GameLoop(GetCharLoop):
        def __init__(self, name, *args, **kwargs):
            self.display_name = name
            self.name = name.replace(' ', '_').lower()
            super().__init__(*args, **kwargs)


if GameLoop:
    name = ih.user_input('\nwhat is the character name')

    # Keyboard shortcuts that work when the gameloop is running
    chfunc = {
        'h': (partial(CharacterController.move_left, name, 1), 'move left 1 space'),
        'l': (partial(CharacterController.move_right, name, 1), 'move right 1 space'),
        'k': (partial(CharacterController.move_up, name, 1), 'move up 1 space'),
        'j': (partial(CharacterController.move_down, name, 1), 'move down 1 space'),
        'H': (partial(CharacterController.move_left, name, 5), 'move left 5 spaces'),
        'L': (partial(CharacterController.move_right, name, 5), 'move right 5 spaces'),
        'K': (partial(CharacterController.move_up, name, 5), 'move up 5 spaces'),
        'J': (partial(CharacterController.move_down, name, 5), 'move down 5 spaces'),
        'p': (partial(CharacterController.get_position, name), 'current position'),
    }

    gameloop = GameLoop(name, chfunc_dict=chfunc, prompt='game-repl> ')

if __name__ == '__main__':
    if GameLoop:
        logger.info('Starting the gameloop...')
        gameloop()
    else:
        logger.info('Explore the following objects: PLAYERS, CHARACTERS, ITEMS, MESSAGES, Player, CharacterController')
