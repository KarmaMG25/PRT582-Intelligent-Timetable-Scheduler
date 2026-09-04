"""Intelligent Timetable Scheduler.

A small deterministic scheduler created for PRT582 to demonstrate
AI-assisted Test-Driven Development and constraint-based scheduling.
"""

from __future__ import annotations


def _positive_int(value, field_name):
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero")


def validate_inputs(courses, rooms, time_slots, lecturer_availability):
    """Validate the small in-memory dataset used by the scheduler."""
    if not isinstance(courses, list) or not isinstance(rooms, list):
        raise TypeError("courses and rooms must be lists")
    if not isinstance(time_slots, list):
        raise TypeError("time_slots must be a list")
    if not isinstance(lecturer_availability, dict):
        raise TypeError("lecturer_availability must be a dictionary")

    known_slots = set(time_slots)
    codes = []

    for room in rooms:
        if not room.get("name"):
            raise ValueError("room name is required")
        _positive_int(room.get("capacity"), "room capacity")

    for course in courses:
        code = course.get("code")
        lecturer = course.get("lecturer")
        if not code:
            raise ValueError("course code is required")
        if not lecturer:
            raise ValueError("lecturer is required")
        _positive_int(course.get("students"), "student count")
        codes.append(code)

    if len(codes) != len(set(codes)):
        raise ValueError("duplicate course codes are not allowed")

    code_set = set(codes)
    for course in courses:
        prerequisite = course.get("prerequisite")
        if prerequisite is not None and prerequisite not in code_set:
            raise ValueError(
                f"unknown prerequisite {prerequisite!r} for course {course['code']}"
            )

    for lecturer, slots in lecturer_availability.items():
        if not isinstance(slots, list):
            raise TypeError(f"availability for {lecturer} must be a list")
        unknown = set(slots) - known_slots
        if unknown:
            raise ValueError(f"unknown time slot(s) for {lecturer}: {sorted(unknown)}")


def is_room_suitable(course, room):
    """Return True when a room can hold all students in a course."""
    _positive_int(course.get("students"), "student count")
    _positive_int(room.get("capacity"), "room capacity")
    return room["capacity"] >= course["students"]


def is_lecturer_available(lecturer, slot, lecturer_availability):
    """Return True when lecturer is listed as available for the slot."""
    return slot in lecturer_availability.get(lecturer, [])


def has_room_clash(timetable, room_name, slot):
    """Return True if the room is already used at the requested slot."""
    return any(
        item["room"] == room_name and item["slot"] == slot
        for item in timetable
    )


def has_lecturer_clash(timetable, lecturer, slot):
    """Return True if the lecturer is already teaching at the requested slot."""
    return any(
        item["lecturer"] == lecturer and item["slot"] == slot
        for item in timetable
    )


def prerequisite_satisfied(course, timetable, slot, time_slots):
    """Check that a prerequisite, if present, is scheduled earlier."""
    prerequisite = course.get("prerequisite")
    if not prerequisite:
        return True

    prereq_entry = next(
        (item for item in timetable if item["course"] == prerequisite), None
    )
    if prereq_entry is None:
        return False

    return time_slots.index(prereq_entry["slot"]) < time_slots.index(slot)


def _ordered_slots(course, time_slots):
    """Return preferred slot first, followed by the remaining slots."""
    preferred = course.get("preferred_slot")
    if preferred in time_slots:
        return [preferred] + [slot for slot in time_slots if slot != preferred]
    return list(time_slots)


def _order_courses_by_prerequisite(courses):
    """Return courses in prerequisite-safe order using a small topological sort."""
    by_code = {course["code"]: course for course in courses}
    ordered = []
    visiting = set()
    visited = set()

    def visit(code):
        if code in visited:
            return
        if code in visiting:
            raise ValueError("cyclic prerequisite relationship detected")
        visiting.add(code)
        course = by_code[code]
        prerequisite = course.get("prerequisite")
        if prerequisite:
            visit(prerequisite)
        visiting.remove(code)
        visited.add(code)
        ordered.append(course)

    for course in courses:
        visit(course["code"])
    return ordered


def generate_timetable(courses, rooms, time_slots, lecturer_availability):
    """Generate a deterministic timetable and list any unscheduled courses.

    The first valid room/slot combination is chosen. A preferred slot is tried
    first when supplied. The function returns:
        {"timetable": [...], "unscheduled": [...]}
    """
    validate_inputs(courses, rooms, time_slots, lecturer_availability)

    timetable = []
    unscheduled = []

    for course in _order_courses_by_prerequisite(courses):
        scheduled = False
        for slot in _ordered_slots(course, time_slots):
            lecturer = course["lecturer"]
            if not is_lecturer_available(lecturer, slot, lecturer_availability):
                continue
            if has_lecturer_clash(timetable, lecturer, slot):
                continue
            if not prerequisite_satisfied(course, timetable, slot, time_slots):
                continue

            for room in rooms:
                if not is_room_suitable(course, room):
                    continue
                if has_room_clash(timetable, room["name"], slot):
                    continue

                timetable.append(
                    {
                        "course": course["code"],
                        "lecturer": lecturer,
                        "room": room["name"],
                        "slot": slot,
                    }
                )
                scheduled = True
                break

            if scheduled:
                break

        if not scheduled:
            unscheduled.append(course["code"])

    return {"timetable": timetable, "unscheduled": unscheduled}
