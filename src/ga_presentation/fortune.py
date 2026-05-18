from __future__ import annotations

from dataclasses import dataclass
import math

from .structures import Arc, Event, Point, PriorityQueue, Segment


EPSILON = 1e-9
PointTuple = tuple[float, float]


@dataclass
class FortuneSnapshot:
    event_kind: str
    sweep_x: float
    focus: PointTuple | None
    processed_sites: list[PointTuple]
    pending_site_count: int
    pending_circle_count: int
    pending_sites: list[PointTuple]
    pending_circles: list[tuple[float, PointTuple]]
    arc_sites: list[PointTuple]
    beachline: list[list[PointTuple]]
    finished_segments: list[tuple[PointTuple, PointTuple]]
    active_segments: list[tuple[PointTuple, PointTuple]]
    voronoi_dual_pairs: list[dict[str, object]]
    delaunay_edges: list[tuple[PointTuple, PointTuple]]
    active_circle_center: PointTuple | None
    active_circle_radius: float | None
    active_circle_sites: list[PointTuple]
    action_summary: str


class FortuneVoronoi:
    def __init__(self, points: list[PointTuple], bounds: tuple[float, float, float, float]) -> None:
        self.output: list[Segment] = []
        self.root_arc: Arc | None = None
        self.site_events = PriorityQueue()
        self.circle_events = PriorityQueue()
        self.triangles: list[tuple[Point, Point, Point]] = []
        self.snapshots: list[FortuneSnapshot] = []
        self.processed_sites: list[PointTuple] = []
        self.min_x, self.max_x, self.min_y, self.max_y = bounds

        dx = (self.max_x - self.min_x + 1.0) / 5.0
        dy = (self.max_y - self.min_y + 1.0) / 5.0
        self.min_x -= dx
        self.max_x += dx
        self.min_y -= dy
        self.max_y += dy

        for x, y in points:
            site = Point(float(x), float(y))
            self.site_events.push(site, site.x)

    def process(self, capture: bool = True) -> None:
        while not self.site_events.empty():
            next_site = self.site_events.top()
            if not self.circle_events.empty() and self.circle_events.top().x <= next_site.x:
                self._process_circle_event(capture)
            else:
                self._process_site_event(capture)

        while not self.circle_events.empty():
            self._process_circle_event(capture)

        self._finish_edges()
        if capture:
            self._capture_snapshot("done", self.max_x, None, action_summary="finish remaining edges")

    def _process_site_event(self, capture: bool) -> None:
        site = self.site_events.pop()
        self.processed_sites.append(site.as_tuple())
        self._insert_arc(site)
        if capture:
            self._capture_snapshot("site", round(site.x, 2), tuple(round(v, 2) for v in site.as_tuple()), action_summary=f"insert site at {tuple(round(v, 2) for v in site.as_tuple())}")


    def _process_circle_event(self, capture: bool) -> None:
        event = self.circle_events.pop()
        if not event.valid:
            return

        arc = event.arc
        circle_sites: list[PointTuple] = []
        circle_radius: float | None = None
        if arc.previous is not None and arc.next is not None:
            self.triangles.append((arc.previous.site, arc.site, arc.next.site))
            circle_sites = [arc.previous.site.as_tuple(), arc.site.as_tuple(), arc.next.site.as_tuple()]
            circle_radius = math.dist(event.center.as_tuple(), arc.site.as_tuple())

        segment = Segment(event.center)
        self.output.append(segment)

        if arc.previous is not None:
            arc.previous.next = arc.next
            arc.previous.right_segment = segment
        if arc.next is not None:
            arc.next.previous = arc.previous
            arc.next.left_segment = segment

        if arc.left_segment is not None:
            arc.left_segment.finish(event.center)
        if arc.right_segment is not None:
            arc.right_segment.finish(event.center)

        if arc.previous is not None:
            self._check_circle_event(arc.previous, event.x)
        if arc.next is not None:
            self._check_circle_event(arc.next, event.x)

        if capture:
            self._capture_snapshot(
                "circle",
                event.x,
                event.center.as_tuple(),
                active_circle_center=event.center.as_tuple(),
                active_circle_radius=circle_radius,
                active_circle_sites=circle_sites,
                action_summary=f"remove disappearing arc at {tuple(round(v, 2) for v in event.center.as_tuple())}"
,
            )

    def _insert_arc(self, site: Point) -> None:
        if self.root_arc is None:
            self.root_arc = Arc(site)
            return

        if abs(self.root_arc.site.x - site.x) < EPSILON:
            site = Point(site.x + EPSILON, site.y)

        arc = self.root_arc
        while arc is not None:
            hit, start = self._intersects(site, arc)
            if hit:
                hit_next, _ = self._intersects(site, arc.next)
                if arc.next is not None and not hit_next:
                    arc.next.previous = Arc(arc.site, arc, arc.next)
                    arc.next = arc.next.previous
                else:
                    arc.next = Arc(arc.site, arc)
                arc.next.right_segment = arc.right_segment

                arc.next.previous = Arc(site, arc, arc.next)
                arc.next = arc.next.previous
                arc = arc.next

                left_segment = Segment(start, arc.previous.site, arc.site)
                right_segment = Segment(start, arc.previous.site, arc.site)
                self.output.extend([left_segment, right_segment])

                arc.previous.right_segment = arc.left_segment = left_segment
                arc.next.left_segment = arc.right_segment = right_segment

                self._check_circle_event(arc, site.x)
                self._check_circle_event(arc.previous, site.x)
                self._check_circle_event(arc.next, site.x)
                return
            arc = arc.next

        arc = self.root_arc
        while arc.next is not None:
            arc = arc.next
        arc.next = Arc(site, arc)

        start = Point(self.min_x, (arc.site.y + arc.next.site.y) / 2.0)
        segment = Segment(start, arc.site, arc.next.site)
        arc.right_segment = arc.next.left_segment = segment
        self.output.append(segment)

    def _intersects(self, site: Point, arc: Arc | None) -> tuple[bool, Point | None]:
        if arc is None or abs(arc.site.x - site.x) < EPSILON:
            return False, None

        lower_y = self.min_y
        upper_y = self.max_y
        if arc.previous is not None:
            lower_y = self._parabola_intersection(arc.previous.site, arc.site, site.x).y
        if arc.next is not None:
            upper_y = self._parabola_intersection(arc.site, arc.next.site, site.x).y

        if lower_y <= site.y <= upper_y:
            px = ((arc.site.x ** 2 + (arc.site.y - site.y) ** 2 - site.x ** 2) / (2 * arc.site.x - 2 * site.x))
            return True, Point(px, site.y)
        return False, None

    def _check_circle_event(self, arc: Arc | None, sweep_x: float) -> None:
        if arc is None:
            return
        if arc.event is not None and abs(arc.event.x - sweep_x) > EPSILON:
            arc.event.valid = False
        arc.event = None

        if arc.previous is None or arc.next is None:
            return

        valid, event_x, center = self._circle(arc.previous.site, arc.site, arc.next.site)
        if valid and event_x > sweep_x:
            arc.event = Event(event_x, center, arc)
            self.circle_events.push(arc.event, arc.event.x)

    def _circle(self, a: Point, b: Point, c: Point) -> tuple[bool, float | None, Point | None]:
        if ((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) > 0:
            return False, None, None

        ax = b.x - a.x
        ay = b.y - a.y
        bx = c.x - a.x
        by = c.y - a.y
        e = ax * (a.x + b.x) + ay * (a.y + b.y)
        f = bx * (a.x + c.x) + by * (a.y + c.y)
        g = 2.0 * (ax * (c.y - b.y) - ay * (c.x - b.x))

        if abs(g) < EPSILON:
            return False, None, None

        center_x = (by * e - ay * f) / g
        center_y = (ax * f - bx * e) / g
        radius = math.sqrt((a.x - center_x) ** 2 + (a.y - center_y) ** 2)
        return True, center_x + radius, Point(center_x, center_y)

    def _parabola_intersection(self, left: Point, right: Point, directrix_x: float) -> Point:
        focus = left
        if abs(left.x - right.x) < EPSILON:
            py = (left.y + right.y) / 2.0
        elif abs(right.x - directrix_x) < EPSILON:
            py = right.y
        elif abs(left.x - directrix_x) < EPSILON:
            py = left.y
            focus = right
        else:
            z0 = 2.0 * (left.x - directrix_x)
            z1 = 2.0 * (right.x - directrix_x)
            a = 1.0 / z0 - 1.0 / z1
            b = -2.0 * (left.y / z0 - right.y / z1)
            c = (
                (left.y ** 2 + left.x ** 2 - directrix_x ** 2) / z0
                - (right.y ** 2 + right.x ** 2 - directrix_x ** 2) / z1
            )
            discriminant = max(b * b - 4.0 * a * c, 0.0)
            py = (-b - math.sqrt(discriminant)) / (2.0 * a)

        px = ((focus.x ** 2 + (focus.y - py) ** 2 - directrix_x ** 2) / (2.0 * focus.x - 2.0 * directrix_x))
        return Point(px, py)

    def _finish_edges(self) -> None:
        directrix_x = self.max_x * 2.0
        arc = self.root_arc
        while arc is not None and arc.next is not None:
            if arc.right_segment is not None:
                arc.right_segment.finish(self._parabola_intersection(arc.site, arc.next.site, directrix_x))
            arc = arc.next

    def _capture_snapshot(
        self,
        event_kind: str,
        sweep_x: float,
        focus: PointTuple | None,
        active_circle_center: PointTuple | None = None,
        active_circle_radius: float | None = None,
        active_circle_sites: list[PointTuple] | None = None,
        action_summary: str = "",
    ) -> None:
        arc_sites: list[PointTuple] = []
        arc = self.root_arc
        while arc is not None:
            arc_sites.append(arc.site.as_tuple())
            arc = arc.next

        finished_segments: list[tuple[PointTuple, PointTuple]] = []
        active_segments: list[tuple[PointTuple, PointTuple]] = []
        voronoi_dual_pairs: list[dict[str, object]] = []
        for segment in self.output:
            if segment.end is not None:
                finished_segments.append((segment.start.as_tuple(), segment.end.as_tuple()))
                if segment.left is not None and segment.right is not None:
                    voronoi_dual_pairs.append(
                        {
                            "voronoi": (segment.start.as_tuple(), segment.end.as_tuple()),
                            "dual": tuple(sorted((segment.left.as_tuple(), segment.right.as_tuple()))),
                        }
                    )

        seen_segment_ids: set[int] = set()
        arc = self.root_arc
        while arc is not None and arc.next is not None:
            segment = arc.right_segment
            if segment is not None and segment.end is None and id(segment) not in seen_segment_ids:
                seen_segment_ids.add(id(segment))
                try:
                    breakpoint = self._parabola_intersection(arc.site, arc.next.site, sweep_x)
                    active_segments.append((segment.start.as_tuple(), breakpoint.as_tuple()))
                except ZeroDivisionError:
                    pass
            arc = arc.next

        delaunay_edges: set[tuple[PointTuple, PointTuple]] = set()
        for a, b, c in self.triangles:
            for start, end in ((a, b), (b, c), (c, a)):
                start_tuple = start.as_tuple()
                end_tuple = end.as_tuple()
                edge = tuple(sorted((start_tuple, end_tuple)))
                delaunay_edges.add(edge)

        pending_sites: list[PointTuple] = []
        for priority, _, item in sorted(self.site_events._entries.values()):
            if item is not None:
                pending_sites.append(item.as_tuple())

        pending_circles: list[tuple[float, PointTuple]] = []
        for priority, _, item in sorted(self.circle_events._entries.values()):
            if item is not None and item.valid:
                pending_circles.append((float(priority), item.center.as_tuple()))

        self.snapshots.append(
            FortuneSnapshot(
                event_kind=event_kind,
                sweep_x=sweep_x,
                focus=focus,
                processed_sites=self.processed_sites[:],
                pending_site_count=len(self.site_events._entries),
                pending_circle_count=len(self.circle_events._entries),
                pending_sites=pending_sites,
                pending_circles=pending_circles,
                arc_sites=arc_sites,
                beachline=self.beachline_polylines(sweep_x),
                finished_segments=finished_segments,
                active_segments=active_segments,
                voronoi_dual_pairs=voronoi_dual_pairs,
                delaunay_edges=sorted(delaunay_edges),
                active_circle_center=active_circle_center,
                active_circle_radius=active_circle_radius,
                active_circle_sites=active_circle_sites or [],
                action_summary=action_summary,
            )
        )

    def beachline_polylines(
        self,
        sweep_x: float,
        sample_count: int = 40,
    ) -> list[list[PointTuple]]:
        if self.root_arc is None:
            return []

        polylines: list[list[PointTuple]] = []
        arc = self.root_arc
        while arc is not None:
            low_y = self.min_y
            high_y = self.max_y
            if arc.previous is not None:
                low_y = self._parabola_intersection(arc.previous.site, arc.site, sweep_x).y
            if arc.next is not None:
                high_y = self._parabola_intersection(arc.site, arc.next.site, sweep_x).y

            if high_y - low_y < EPSILON:
                arc = arc.next
                continue

            points: list[PointTuple] = []
            for index in range(sample_count):
                t = index / max(sample_count - 1, 1)
                y = low_y + (high_y - low_y) * t
                denominator = 2.0 * arc.site.x - 2.0 * sweep_x
                if abs(denominator) < EPSILON:
                    continue
                x = ((arc.site.x ** 2 + (arc.site.y - y) ** 2 - sweep_x ** 2) / denominator)
                points.append((x, y))

            if points:
                polylines.append(points)
            arc = arc.next

        return polylines


def compute_voronoi(points: list[PointTuple], bounds: tuple[float, float, float, float], capture: bool = True) -> FortuneVoronoi:
    voronoi = FortuneVoronoi(points, bounds)
    voronoi.process(capture=capture)
    return voronoi
