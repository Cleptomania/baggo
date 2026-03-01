from enum import IntEnum
import random

import baggo
from baggo import to_cp437

from rect import Rect
from components import Position


class TileType(IntEnum):
    FLOOR = to_cp437(".")
    WALL = to_cp437("#")


class LevelGenerator:
    OLD = 0
    ROOMS = 1


class Level(baggo.Map2D):
    tiles: list[TileType]

    def __init__(
        self, width: int, height: int, generator: LevelGenerator = LevelGenerator.ROOMS
    ):
        self.spawn_point = Position(0, 0)

        match generator:
            case LevelGenerator.OLD:
                self.generate_level_old()
            case LevelGenerator.ROOMS:
                self.generate_level_rooms()

    def is_opaque(self, x: int, y: int) -> bool:
        return self.get_tile(x, y) == TileType.WALL

    def get_tile(self, x: int, y: int) -> TileType:
        return self.tiles[self.index(x, y)]

    def draw(self, console: baggo.Console):
        x = 0
        y = 0
        for tile in self.tiles:
            match tile:
                case TileType.FLOOR:
                    console.set(
                        x, y, TileType.FLOOR, baggo.colors.GRAY, baggo.colors.BLACK
                    )
                case TileType.WALL:
                    console.set(
                        x, y, TileType.WALL, baggo.colors.SAP_GREEN, baggo.colors.BLACK
                    )
            x += 1
            if x >= self.width:
                x = 0
                y += 1

    def moveable(self, x: int, y: int) -> bool:
        return self.get_tile(x, y) != TileType.WALL

    def generate_level_old(self) -> None:
        # First populate the level with floor
        self.spawn_point.x = 40
        self.spawn_point.y = 25
        self.tiles = [TileType.FLOOR] * (self.width * self.height)

        # Then add in walls around the borders
        for x in range(self.width):
            self.tiles[self.index(x, 0)] = TileType.WALL
            self.tiles[self.index(x, self.height - 1)] = TileType.WALL

        for y in range(self.height):
            self.tiles[self.index(0, y)] = TileType.WALL
            self.tiles[self.index(self.width - 1, y)] = TileType.WALL

        # Lastly place some walls randomly throughout the level
        for i in range(400):
            x = random.randint(1, self.width - 1)
            y = random.randint(1, self.height - 1)
            index = self.index(x, y)
            if index != self.index(
                40, 25
            ):  # Don't put a wall where the player spawn is
                self.tiles[index] = TileType.WALL

    def create_room(self, room: Rect) -> None:
        for y in range(room.y1 + 1, room.y2):
            for x in range(room.x1 + 1, room.x2):
                self.tiles[self.index(x, y)] = TileType.FLOOR

    def tunnel_horizontal(self, x1: int, x2: int, y: int) -> None:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            index = self.index(x, y)
            if 0 < index < len(self.tiles):
                self.tiles[index] = TileType.FLOOR

    def tunnel_vertical(self, y1: int, y2: int, x: int) -> None:
        for y in range(min(y1, y2), max(y1, y2) + 1):
            index = self.index(x, y)
            if 0 < index < len(self.tiles):
                self.tiles[index] = TileType.FLOOR

    def generate_level_rooms(self) -> None:
        # First populate whole level with walls, we will then "dig out" rooms and tunnels
        self.tiles = [TileType.WALL] * (self.width * self.height)

        rooms = []
        MAX_ROOMS = 30
        MIN_SIZE = 6
        MAX_SIZE = 10

        for i in range(MAX_ROOMS):
            # Create a rectangle to represent our new room
            w = random.randint(MIN_SIZE, MAX_SIZE)
            h = random.randint(MIN_SIZE, MAX_SIZE)
            x = random.randint(1, self.width - w - 1) - 1
            y = random.randint(1, self.height - h - 1) - 1
            new_room = Rect(x, y, w, h)

            # Check if the new room intersects an already existing room
            can_build = True
            for other_room in rooms:
                if new_room.intersects(other_room):
                    can_build = False

            # If it does intersect, we will jsut move on and not build it
            if not can_build:
                continue

            self.create_room(new_room)

            # We will dug tunnels now, but we need to make sure we already have another room
            # As we can't dig tunnels from the first room, as the tunnel digging is designed to
            # connect rooms that exist.
            if len(rooms) > 0:
                new_center = new_room.center()
                prev_center = rooms[len(rooms) - 1].center()

                # This randomization decides which room the tunnel will be centered on
                if bool(random.getrandbits(1)):
                    self.tunnel_horizontal(
                        prev_center[0], new_center[0], prev_center[1]
                    )
                    self.tunnel_vertical(prev_center[1], new_center[1], new_center[0])
                else:
                    self.tunnel_vertical(prev_center[1], new_center[1], prev_center[0])
                    self.tunnel_horizontal(prev_center[0], new_center[0], new_center[1])

            rooms.append(new_room)

        center = rooms[0].center()
        self.spawn_point = Position(center[0], center[1])
