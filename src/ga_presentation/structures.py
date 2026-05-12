from __future__ import annotations

from dataclasses import dataclass
import heapq
import itertools


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def as_tuple(self) -> tuple[float, float]:
        return (self.x, self.y)


@dataclass(eq=False)
class Event:
    x: float
    center: Point
    arc: "Arc"
    valid: bool = True


@dataclass
class Segment:
    start: Point
    left: Point | None = None
    right: Point | None = None
    end: Point | None = None
    done: bool = False

    def finish(self, end: Point) -> None:
        if self.done:
            return
        self.end = end
        self.done = True


class Arc:
    def __init__(self, site: Point, previous: "Arc | None" = None, next_arc: "Arc | None" = None):
        self.site = site
        self.previous = previous
        self.next = next_arc
        self.event: Event | None = None
        self.left_segment: Segment | None = None
        self.right_segment: Segment | None = None


class PriorityQueue:
    def __init__(self) -> None:
        self._heap: list[list[object]] = []
        self._entries: dict[object, list[object]] = {}
        self._counter = itertools.count()

    def push(self, item: object, priority: float) -> None:
        if item in self._entries:
            return
        entry = [priority, next(self._counter), item]
        self._entries[item] = entry
        heapq.heappush(self._heap, entry)

    def pop(self) -> object:
        while self._heap:
            priority, _, item = heapq.heappop(self._heap)
            if item is not None:
                del self._entries[item]
                return item
        raise KeyError("pop from empty priority queue")

    def top(self) -> object:
        while self._heap:
            priority, _, item = heapq.heappop(self._heap)
            if item is not None:
                del self._entries[item]
                self.push(item, float(priority))
                return item
        raise KeyError("top from empty priority queue")

    def discard(self, item: object) -> None:
        entry = self._entries.pop(item, None)
        if entry is not None:
            entry[-1] = None

    def empty(self) -> bool:
        return not self._entries
