class Rect:

    def __init__(self, x: int, y: int, w: int, h: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def intersects(self, other: Rect) -> bool:
        return self.x1 < other.x2 and self.x2 >= other.x1 and self.y1 < other.y2 and self.y2 >= other.y1

    def center(self) -> tuple[int, int]:
        return (self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2
