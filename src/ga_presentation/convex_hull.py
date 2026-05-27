from __future__ import annotations

from dataclasses import dataclass
import math

from .structures import Point

PointTuple = tuple[float, float]
p = Point | PointTuple


@dataclass # x visualization
class HullSnapshot:
    pivot: p
    sorted_points: list[p]
    action: str
    candidate: p
    stack_before: list[p]
    stack: list[p]
    test_points: tuple[p, p, p] | None
    orientation_value: float | None

# >0 left, <0 right, = colinear 
def orientation(a: p, b: p, c: p) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def monotone_chain(points: list[p]) -> tuple[list[p], list[HullSnapshot]]:
    unique_points = sorted(set(points), key=lambda point: (point[0], point[1])) # Sort for increasing X, then Y
    if len(unique_points) < 3: # at least 3 or return
        return unique_points[:], [
            HullSnapshot(point, unique_points[:], "seed", point, [], [point], None, None)
            for point in unique_points
        ]

    start = unique_points[0]  # take min left

    stack: list[p] = []
    snapshots: list[HullSnapshot] = []

    # Lower chain (from left to right)
    for point in unique_points:
        # check if turn left, otherwise remove the last point
        while len(stack) >= 2:
            before_stack = stack[:]
            turn_value = orientation(stack[-2], stack[-1], point)
            if turn_value > 0: #turn left
                break
            stack.pop() # else pop
            snapshots.append(
                HullSnapshot(start,unique_points[:],"pop",point,before_stack,stack[:],(before_stack[-2], before_stack[-1], point),turn_value,)
            )

        # insert in the stack
        before_stack = stack[:]
        stack.append(point)

        # check orientation
        test_points = (before_stack[-2], before_stack[-1], point) if len(before_stack) >= 2 else None
        turn_value = orientation(*test_points) if test_points else None
        #visualization
        snapshots.append(
            HullSnapshot(
                start, unique_points[:], "push", point, 
                before_stack, stack[:], test_points, turn_value)
        )

    # save lower chain position, upper chain will be appended from here
    lower_hull_size = len(stack)

    # Upper chain, right to left.
    # last point, the rightmost, is already insert
    for point in reversed(unique_points[:-1]):
        while len(stack) > lower_hull_size:
            before_stack = stack[:] # points to evaluate with orientation_test
            turn_value = orientation(stack[-2], stack[-1], point)
            if turn_value > 0: #left turn
                break
            stack.pop() #else pop
            #visualization
            snapshots.append(
                HullSnapshot(
                    start, unique_points[:], "pop", point, before_stack, stack[:],
                    (before_stack[-2], before_stack[-1], point), turn_value
                )
            )
        before_stack = stack[:] # points to evaluate with orientation_test
        stack.append(point)

        #orientation test
        test_points = (before_stack[-2], before_stack[-1], point) if len(before_stack) >= 2 else None

        turn_value = orientation(*test_points) if test_points else None #orientation test

        snapshots.append(HullSnapshot(start, unique_points[:], "push", point, before_stack, stack[:], test_points, turn_value))

    # last element == first element in a CH. Must be removed
    stack.pop() 
    
    return stack, snapshots
