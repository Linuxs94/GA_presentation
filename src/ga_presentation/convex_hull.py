from __future__ import annotations

from dataclasses import dataclass
import math

from .structures import Point

PointTuple = tuple[float, float]
PointLike = Point | PointTuple


@dataclass
class HullSnapshot:
    pivot: PointLike
    sorted_points: list[PointLike]
    action: str
    candidate: PointLike
    stack_before: list[PointLike]
    stack: list[PointLike]
    test_points: tuple[PointLike, PointLike, PointLike] | None
    orientation_value: float | None


def orientation(a: PointLike, b: PointLike, c: PointLike) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def graham_scan(points: list[PointLike]) -> tuple[list[PointLike], list[HullSnapshot]]:
    unique_points = sorted(set(points), key=lambda point: (point[0], point[1]))
    if len(unique_points) < 3:
        return unique_points[:], [
            HullSnapshot(point, unique_points[:], "seed", point, [], [point], None, None)
            for point in unique_points
        ]

    pivot = min(unique_points, key=lambda point: (point[1], point[0]))

    def polar_angle(point: PointLike) -> float:
        return math.atan2(point[1] - pivot[1], point[0] - pivot[0])

    sorted_points = [pivot] + sorted(
        (point for point in unique_points if point != pivot),
        key=lambda point: (polar_angle(point), math.dist(pivot, point)),
    )

    stack: list[PointLike] = []
    snapshots: list[HullSnapshot] = []

    for point in sorted_points:
        # Remove the last point while the hull would turn clockwise or stay flat.
        while len(stack) >= 2:
            before_stack = stack[:]
            turn_value = orientation(stack[-2], stack[-1], point)
            if turn_value > 0:
                break
            stack.pop()
            snapshots.append(
                HullSnapshot(
                    pivot,
                    sorted_points[:],
                    "pop",
                    point,
                    before_stack,
                    stack[:],
                    (before_stack[-2], before_stack[-1], point),
                    turn_value,
                )
            )
        before_stack = stack[:]
        stack.append(point)
        test_points = None
        turn_value = None
        if len(before_stack) >= 2:
            test_points = (before_stack[-2], before_stack[-1], point)
            turn_value = orientation(*test_points)
        snapshots.append(
            HullSnapshot(
                pivot,
                sorted_points[:],
                "push",
                point,
                before_stack,
                stack[:],
                test_points,
                turn_value,
            )
        )

    return stack, snapshots
