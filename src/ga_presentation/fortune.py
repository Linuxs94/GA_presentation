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
    decision: str
    processed_sites: list[PointTuple]
    pending_site_count: int
    pending_circle_count: int
    pending_sites: list[PointTuple]
    pending_circles: list[tuple[float, PointTuple]]
    arc_sites: list[PointTuple]
    beachline: list[list[PointTuple]]
    finished_segments: list[tuple[PointTuple, PointTuple]]
    active_segments: list[tuple[PointTuple, PointTuple]]
    carried_finished_segments: list[tuple[PointTuple, PointTuple]]
    carried_active_segments: list[tuple[PointTuple, PointTuple]]
    # voronoi edge <-> delaunay edge relation
    voronoi_dual_pairs: list[dict[str, object]]
    # final delaunay edges
    delaunay_edges: list[tuple[PointTuple, PointTuple]]
    active_circle_center: PointTuple | None
    active_circle_radius: float | None
    active_circle_sites: list[PointTuple]
    affected_arc_site: PointTuple | None
    removed_arc_site: PointTuple | None
    created_arc_sites: list[PointTuple]
    created_segments_this_step: list[dict[str, object]]
    finished_segments_this_step: list[tuple[PointTuple, PointTuple]]
    new_active_segments_this_step: list[tuple[PointTuple, PointTuple]]
    circle_events_added_this_step: list[dict[str, object]]
    circle_events_invalidated_this_step: list[dict[str, object]]
    new_delaunay_edges: list[tuple[PointTuple, PointTuple]]
    camera_bounds: tuple[float, float, float, float]
    action_summary: str


class FortuneVoronoi:
    def __init__(self, points: list[PointTuple], bounds: tuple[float, float, float, float]) -> None:
        self.output: list[Segment] = []
        # beachline root
        self.root_arc: Arc | None = None
        # events ordered by x
        self.site_events = PriorityQueue()
        self.circle_events = PriorityQueue()
        # delaunay triangles
        self.triangles: list[tuple[Point, Point, Point]] = []
        self.snapshots: list[FortuneSnapshot] = []
        self.processed_sites: list[PointTuple] = []
        self._last_delaunay_edges: set[tuple[PointTuple, PointTuple]] = set()
        self._reset_step_tracking()
        self.min_x, self.max_x, self.min_y, self.max_y = bounds

        dx = (self.max_x - self.min_x + 1.0) / 5.0
        dy = (self.max_y - self.min_y + 1.0) / 5.0
        self.min_x -= dx
        self.max_x += dx
        self.min_y -= dy
        self.max_y += dy

        # push all sites
        for x, y in points:
            site = Point(float(x), float(y))
            self.site_events.push(site, site.x)

    def _reset_step_tracking(self) -> None:
        self._current_decision = ""
        self._current_affected_arc_site: PointTuple | None = None
        self._current_removed_arc_site: PointTuple | None = None
        self._current_created_arc_sites: list[PointTuple] = []
        self._current_created_segments: list[dict[str, object]] = []
        self._current_finished_segments: list[tuple[PointTuple, PointTuple]] = []
        self._current_added_circle_events: list[dict[str, object]] = []
        self._current_invalidated_circle_events: list[dict[str, object]] = []

    def _begin_step_tracking(self, decision: str) -> None:
        self._reset_step_tracking()
        self._current_decision = decision

    def _segment_record(self, segment: Segment) -> dict[str, object]:
        return {
            "start": segment.start.as_tuple(),
            "end": segment.end.as_tuple() if segment.end is not None else None,
            "left": segment.left.as_tuple() if segment.left is not None else None,
            "right": segment.right.as_tuple() if segment.right is not None else None,
            "done": segment.done,
        }

    def _record_created_segment(self, segment: Segment) -> None:
        self._current_created_segments.append(self._segment_record(segment))

    def _record_finished_segment(self, segment: Segment) -> None:
        if segment.end is not None:
            self._current_finished_segments.append((segment.start.as_tuple(), segment.end.as_tuple()))

    def _compute_camera_bounds(
        self,
        focus: PointTuple | None,
        processed_sites: list[PointTuple],
        pending_sites: list[PointTuple],
        finished_segments: list[tuple[PointTuple, PointTuple]],
        active_segments: list[tuple[PointTuple, PointTuple]],
        beachline: list[list[PointTuple]],
        active_circle_center: PointTuple | None,
        active_circle_radius: float | None,
    ) -> tuple[float, float, float, float]:
        points: list[PointTuple] = []
        base_center_x = (self.min_x + self.max_x) * 0.5
        base_center_y = (self.min_y + self.max_y) * 0.5
        base_span_x = max(self.max_x - self.min_x, 1.0)
        base_span_y = max(self.max_y - self.min_y, 1.0)
        limit_x = base_span_x * 2.5
        limit_y = base_span_y * 2.5

        def keep(point: PointTuple) -> bool:
            return (
                math.isfinite(point[0])
                and math.isfinite(point[1])
                and abs(point[0] - base_center_x) <= limit_x
                and abs(point[1] - base_center_y) <= limit_y
            )

        points.extend(point for point in processed_sites if keep(point))
        points.extend(point for point in pending_sites if keep(point))
        if focus is not None:
            if keep(focus):
                points.append(focus)
        for start, end in finished_segments:
            if keep(start):
                points.append(start)
            if keep(end):
                points.append(end)
        for start, end in active_segments:
            if keep(start):
                points.append(start)
            if keep(end):
                points.append(end)
        for polyline in beachline:
            points.extend(point for point in polyline if keep(point))
        if active_circle_center is not None and active_circle_radius is not None:
            cx, cy = active_circle_center
            r = active_circle_radius
            circle_points = [(cx - r, cy - r), (cx - r, cy + r), (cx + r, cy - r), (cx + r, cy + r)]
            points.extend(point for point in circle_points if keep(point))

        if not points:
            return (self.min_x, self.max_x, self.min_y, self.max_y)

        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        min_x = min(xs)
        max_x = max(xs)
        min_y = min(ys)
        max_y = max(ys)
        span_x = max(max_x - min_x, 1.0)
        span_y = max(max_y - min_y, 1.0)
        pad_x = max(span_x * 0.12, 20.0)
        pad_y = max(span_y * 0.12, 20.0)
        return (min_x - pad_x, max_x + pad_x, min_y - pad_y, max_y + pad_y)

    def _record_circle_event_added(self, event: Event, arc: Arc) -> None:
        self._current_added_circle_events.append(
            {
                "event_x": float(event.x),
                "center": event.center.as_tuple(),
                "arc_site": arc.site.as_tuple(),
            }
        )

    def _record_circle_event_invalidated(self, event: Event, arc: Arc) -> None:
        self._current_invalidated_circle_events.append(
            {
                "event_x": float(event.x),
                "center": event.center.as_tuple(),
                "arc_site": arc.site.as_tuple(),
            }
        )

    def process(self, capture: bool = True) -> None:

        # process all events
        while not self.site_events.empty():
            next_site = self.site_events.top()

            # circle event comes first
            if not self.circle_events.empty() and self.circle_events.top().x <= next_site.x:
                self._process_circle_event(capture)

            # site event comes first
            else:
                self._process_site_event(capture)

        # finish remaining circles
        while not self.circle_events.empty():
            self._process_circle_event(capture)

        # close unfinished rays
        if capture:
            self._begin_step_tracking("finish_edges")
        self._finish_edges()
        if capture:
            self._capture_snapshot("done", self.max_x, None, action_summary="finish remaining edges")

    def _process_site_event(self, capture: bool) -> None:
        site = self.site_events.pop()
        self.processed_sites.append(site.as_tuple())
        if capture:
            self._begin_step_tracking("insert_arc")

        # add parabola to beachline
        self._insert_arc(site)
        if capture:
            self._capture_snapshot("site", round(site.x, 2), tuple(round(v, 2) for v in site.as_tuple()), action_summary=f"insert site at {tuple(round(v, 2) for v in site.as_tuple())}")


    def _process_circle_event(self, capture: bool) -> None:
        event = self.circle_events.pop()

        # skip invalidated events
        if not event.valid:
            return

        arc = event.arc
        if capture:
            self._begin_step_tracking("remove_arc")
            self._current_removed_arc_site = arc.site.as_tuple()
        circle_sites: list[PointTuple] = []
        circle_radius: float | None = None

        # 3 neighboring sites form a delaunay triangle
        if arc.previous is not None and arc.next is not None:
            self.triangles.append((arc.previous.site, arc.site, arc.next.site))

            # store sites for visualization
            circle_sites = [arc.previous.site.as_tuple(), arc.site.as_tuple(), arc.next.site.as_tuple()]
            circle_radius = math.dist(event.center.as_tuple(), arc.site.as_tuple())

        # new voronoi vertex
        segment = Segment(event.center)
        self.output.append(segment)
        if capture:
            self._record_created_segment(segment)

        # reconnect beachline
        if arc.previous is not None:
            arc.previous.next = arc.next
            arc.previous.right_segment = segment
        if arc.next is not None:
            arc.next.previous = arc.previous
            arc.next.left_segment = segment

        # finish broken edges
        if arc.left_segment is not None:
            arc.left_segment.finish(event.center)
            if capture:
                self._record_finished_segment(arc.left_segment)
        if arc.right_segment is not None:
            arc.right_segment.finish(event.center)
            if capture:
                self._record_finished_segment(arc.right_segment)

        # new circle checks
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

                # arc disappears here
                action_summary=f"remove disappearing arc at {tuple(round(v, 2) for v in event.center.as_tuple())}"
,
            )

    def _insert_arc(self, site: Point) -> None:

        # first parabola
        if self.root_arc is None:
            self.root_arc = Arc(site)
            self._current_created_arc_sites.append(site.as_tuple())
            return

        # avoid division problems
        if abs(self.root_arc.site.x - site.x) < EPSILON:
            site = Point(site.x + EPSILON, site.y)

        arc = self.root_arc
        while arc is not None:

            # check if site hits this arc
            hit, start = self._intersects(site, arc)
            if hit:
                self._current_affected_arc_site = arc.site.as_tuple()

                # split arc
                hit_next, _ = self._intersects(site, arc.next)
                if arc.next is not None and not hit_next:
                    arc.next.previous = Arc(arc.site, arc, arc.next)
                    arc.next = arc.next.previous
                else:
                    arc.next = Arc(arc.site, arc)
                arc.next.right_segment = arc.right_segment

                # insert new arc
                arc.next.previous = Arc(site, arc, arc.next)
                arc.next = arc.next.previous
                arc = arc.next
                self._current_created_arc_sites.extend(
                    [arc.site.as_tuple(), arc.next.site.as_tuple() if arc.next is not None else arc.site.as_tuple()]
                )

                # create voronoi edges
                left_segment = Segment(start, arc.previous.site, arc.site)
                right_segment = Segment(start, arc.previous.site, arc.site)
                self.output.extend([left_segment, right_segment])
                self._record_created_segment(left_segment)
                self._record_created_segment(right_segment)

                arc.previous.right_segment = arc.left_segment = left_segment
                arc.next.left_segment = arc.right_segment = right_segment

                # check new circles
                self._check_circle_event(arc, site.x)
                self._check_circle_event(arc.previous, site.x)
                self._check_circle_event(arc.next, site.x)
                return
            arc = arc.next

        # insert at end
        arc = self.root_arc
        while arc.next is not None:
            arc = arc.next
        arc.next = Arc(site, arc)
        self._current_affected_arc_site = arc.site.as_tuple()
        self._current_created_arc_sites.append(site.as_tuple())

        # start infinite edge
        start = Point(self.min_x, (arc.site.y + arc.next.site.y) / 2.0)
        segment = Segment(start, arc.site, arc.next.site)
        arc.right_segment = arc.next.left_segment = segment
        self.output.append(segment)
        self._record_created_segment(segment)

    def _intersects(self, site: Point, arc: Arc | None) -> tuple[bool, Point | None]:
        if arc is None or abs(arc.site.x - site.x) < EPSILON:
            return False, None

        lower_y = self.min_y
        upper_y = self.max_y

        # lower breakpoint
        if arc.previous is not None:
            lower_y = self._parabola_intersection(arc.previous.site, arc.site, site.x).y
        # upper breakpoint
        if arc.next is not None:
            upper_y = self._parabola_intersection(arc.site, arc.next.site, site.x).y

        # site falls inside arc
        if lower_y <= site.y <= upper_y:
            px = ((arc.site.x ** 2 + (arc.site.y - site.y) ** 2 - site.x ** 2) / (2 * arc.site.x - 2 * site.x))
            return True, Point(px, site.y)
        return False, None

    def _check_circle_event(self, arc: Arc | None, sweep_x: float) -> None:
        if arc is None:
            return

        # invalidate old event
        if arc.event is not None and abs(arc.event.x - sweep_x) > EPSILON:
            self._record_circle_event_invalidated(arc.event, arc)
            arc.event.valid = False
        arc.event = None

        # need 3 arcs
        if arc.previous is None or arc.next is None:
            return

        # compute circumcircle
        valid, event_x, center = self._circle(arc.previous.site, arc.site, arc.next.site)
        # future circle event
        if valid and event_x > sweep_x:
            arc.event = Event(event_x, center, arc)
            self.circle_events.push(arc.event, arc.event.x)
            self._record_circle_event_added(arc.event, arc)

    def _circle(self, a: Point, b: Point, c: Point) -> tuple[bool, float | None, Point | None]:
        # reject clockwise orientation
        if ((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) > 0:
            return False, None, None

        # shifted coordinates
        ax = b.x - a.x
        ay = b.y - a.y
        bx = c.x - a.x
        by = c.y - a.y

        # circumcenter math
        e = ax * (a.x + b.x) + ay * (a.y + b.y)
        f = bx * (a.x + c.x) + by * (a.y + c.y)
        g = 2.0 * (ax * (c.y - b.y) - ay * (c.x - b.x))

        # collinear points
        if abs(g) < EPSILON:
            return False, None, None

        # circumcenter
        center_x = (by * e - ay * f) / g
        center_y = (ax * f - bx * e) / g

        # circumradius
        radius = math.sqrt((a.x - center_x) ** 2 + (a.y - center_y) ** 2)
        # rightmost point of circle
        return True, center_x + radius, Point(center_x, center_y)

    def _parabola_intersection(self, left: Point, right: Point, directrix_x: float) -> Point:
        focus = left

        # same x
        if abs(left.x - right.x) < EPSILON:
            py = (left.y + right.y) / 2.0

        # degenerate cases
        elif abs(right.x - directrix_x) < EPSILON:
            py = right.y
        elif abs(left.x - directrix_x) < EPSILON:
            py = left.y
            focus = right
        else:

            # parabola equations
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

        # x on parabola
        px = ((focus.x ** 2 + (focus.y - py) ** 2 - directrix_x ** 2) / (2.0 * focus.x - 2.0 * directrix_x))
        return Point(px, py)

    def _finish_edges(self) -> None:
        
        # far away sweep line
        directrix_x = self.max_x * 2.0
        arc = self.root_arc
        while arc is not None and arc.next is not None:

            # extend unfinished edge
            if arc.right_segment is not None:
                arc.right_segment.finish(self._parabola_intersection(arc.site, arc.next.site, directrix_x))
                self._record_finished_segment(arc.right_segment)
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

        # current beachline sites
        arc_sites: list[PointTuple] = []
        arc = self.root_arc
        while arc is not None:
            arc_sites.append(arc.site.as_tuple())
            arc = arc.next

        finished_segments: list[tuple[PointTuple, PointTuple]] = []
        active_segments: list[tuple[PointTuple, PointTuple]] = []

        # voronoi <-> delaunay duality
        voronoi_dual_pairs: list[dict[str, object]] = []
        for segment in self.output:

            # completed voronoi edge
            if segment.end is not None:
                finished_segments.append((segment.start.as_tuple(), segment.end.as_tuple()))

                # every voronoi edge separates 2 sites
                if segment.left is not None and segment.right is not None:
                    voronoi_dual_pairs.append(
                        {
                            # voronoi edge
                            "voronoi": (segment.start.as_tuple(), segment.end.as_tuple()),

                            # delaunay edge
                            "dual": tuple(sorted((segment.left.as_tuple(), segment.right.as_tuple()))),
                        }
                    )

        seen_segment_ids: set[int] = set()
        arc = self.root_arc
        while arc is not None and arc.next is not None:
            segment = arc.right_segment

            # active unfinished edge
            if segment is not None and segment.end is None and id(segment) not in seen_segment_ids:
                seen_segment_ids.add(id(segment))
                try:
                    breakpoint = self._parabola_intersection(arc.site, arc.next.site, sweep_x)
                    active_segments.append((segment.start.as_tuple(), breakpoint.as_tuple()))
                except ZeroDivisionError:
                    pass
            arc = arc.next

        created_segment_starts = {point_key for point_key in [item["start"] for item in self._current_created_segments]}
        created_segments_with_end = [
            segment for segment in active_segments if segment[0] in created_segment_starts
        ]
        finished_set = set(self._current_finished_segments)
        active_set = set(active_segments)
        new_active_set = set(created_segments_with_end)
        carried_finished_segments = [segment for segment in finished_segments if segment not in finished_set]
        carried_active_segments = [segment for segment in active_segments if segment not in new_active_set]

        # delaunay graph
        delaunay_edges: set[tuple[PointTuple, PointTuple]] = set()

        # triangles already found from circle events
        for a, b, c in self.triangles:

            # each triangle gives 3 edges
            for start, end in ((a, b), (b, c), (c, a)):
                start_tuple = start.as_tuple()
                end_tuple = end.as_tuple()

                # normalized edge
                edge = tuple(sorted((start_tuple, end_tuple)))
                delaunay_edges.add(edge)
        new_delaunay_edges = sorted(delaunay_edges - self._last_delaunay_edges)
        self._last_delaunay_edges = set(delaunay_edges)

        pending_sites: list[PointTuple] = []

        # queued site events
        for priority, _, item in sorted(self.site_events._entries.values()):
            if item is not None:
                pending_sites.append(item.as_tuple())

        pending_circles: list[tuple[float, PointTuple]] = []

        # queued circle events
        for priority, _, item in sorted(self.circle_events._entries.values()):
            if item is not None and item.valid:
                pending_circles.append((float(priority), item.center.as_tuple()))

        beachline = self.beachline_polylines(sweep_x)
        camera_bounds = self._compute_camera_bounds(
            focus=focus,
            processed_sites=self.processed_sites[:],
            pending_sites=pending_sites,
            finished_segments=finished_segments,
            active_segments=active_segments,
            beachline=beachline,
            active_circle_center=active_circle_center,
            active_circle_radius=active_circle_radius,
        )

        self.snapshots.append(
            FortuneSnapshot(
                event_kind=event_kind,
                sweep_x=sweep_x,
                focus=focus,
                decision=self._current_decision,
                processed_sites=self.processed_sites[:],
                pending_site_count=len(self.site_events._entries),
                pending_circle_count=len(self.circle_events._entries),
                pending_sites=pending_sites,
                pending_circles=pending_circles,
                arc_sites=arc_sites,
                beachline=beachline,
                finished_segments=finished_segments,
                active_segments=active_segments,
                carried_finished_segments=carried_finished_segments,
                carried_active_segments=carried_active_segments,

                # voronoi edge -> delaunay edge
                voronoi_dual_pairs=voronoi_dual_pairs,

                # current delaunay graph
                delaunay_edges=sorted(delaunay_edges),
                active_circle_center=active_circle_center,
                active_circle_radius=active_circle_radius,
                active_circle_sites=active_circle_sites or [],
                affected_arc_site=self._current_affected_arc_site,
                removed_arc_site=self._current_removed_arc_site,
                created_arc_sites=self._current_created_arc_sites[:],
                created_segments_this_step=self._current_created_segments[:],
                finished_segments_this_step=self._current_finished_segments[:],
                new_active_segments_this_step=created_segments_with_end,
                circle_events_added_this_step=self._current_added_circle_events[:],
                circle_events_invalidated_this_step=self._current_invalidated_circle_events[:],
                new_delaunay_edges=new_delaunay_edges,
                camera_bounds=camera_bounds,
                action_summary=action_summary,
            )
        )
        self._reset_step_tracking()

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

            # lower breakpoint
            if arc.previous is not None:
                low_y = self._parabola_intersection(arc.previous.site, arc.site, sweep_x).y

            # upper breakpoint
            if arc.next is not None:
                high_y = self._parabola_intersection(arc.site, arc.next.site, sweep_x).y

            # skip tiny arc
            if high_y - low_y < EPSILON:
                arc = arc.next
                continue

            points: list[PointTuple] = []

            # sample parabola
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
