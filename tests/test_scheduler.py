import pytest

from scheduler.scheduler import (
    generate_timetable,
    has_lecturer_clash,
    has_room_clash,
    is_lecturer_available,
    is_room_suitable,
    prerequisite_satisfied,
    validate_inputs,
)


# Room-capacity tests: normal + boundary
def test_room_larger_than_class_is_suitable():
    assert is_room_suitable({"students": 25}, {"capacity": 30}) is True


def test_room_equal_to_class_is_suitable():
    assert is_room_suitable({"students": 30}, {"capacity": 30}) is True


def test_room_one_seat_too_small_is_rejected():
    assert is_room_suitable({"students": 31}, {"capacity": 30}) is False


# Lecturer availability tests
def test_available_lecturer_is_accepted():
    availability = {"Alice": ["Mon 09:00"]}
    assert is_lecturer_available("Alice", "Mon 09:00", availability) is True


def test_unavailable_lecturer_is_rejected():
    availability = {"Alice": ["Tue 09:00"]}
    assert is_lecturer_available("Alice", "Mon 09:00", availability) is False


# Clash tests
def test_room_clash_is_detected():
    timetable = [{"course": "A", "lecturer": "L1", "room": "R1", "slot": "Mon 09:00"}]
    assert has_room_clash(timetable, "R1", "Mon 09:00") is True


def test_same_room_different_slot_is_not_a_clash():
    timetable = [{"course": "A", "lecturer": "L1", "room": "R1", "slot": "Mon 09:00"}]
    assert has_room_clash(timetable, "R1", "Mon 11:00") is False


def test_lecturer_clash_is_detected():
    timetable = [{"course": "A", "lecturer": "L1", "room": "R1", "slot": "Mon 09:00"}]
    assert has_lecturer_clash(timetable, "L1", "Mon 09:00") is True


def test_same_lecturer_different_slot_is_not_a_clash():
    timetable = [{"course": "A", "lecturer": "L1", "room": "R1", "slot": "Mon 09:00"}]
    assert has_lecturer_clash(timetable, "L1", "Mon 11:00") is False


# Prerequisite tests
def test_prerequisite_must_be_earlier():
    slots = ["Mon 09:00", "Mon 11:00"]
    timetable = [{"course": "PRT100", "lecturer": "L1", "room": "R1", "slot": "Mon 09:00"}]
    course = {"code": "PRT200", "prerequisite": "PRT100"}
    assert prerequisite_satisfied(course, timetable, "Mon 11:00", slots) is True


def test_missing_prerequisite_is_not_satisfied():
    slots = ["Mon 09:00", "Mon 11:00"]
    course = {"code": "PRT200", "prerequisite": "PRT100"}
    assert prerequisite_satisfied(course, [], "Mon 11:00", slots) is False


# Preferred-slot + complete scheduling tests
def test_scheduler_uses_valid_preferred_slot():
    courses = [
        {"code": "PRT582", "students": 25, "lecturer": "Alice",
         "preferred_slot": "Mon 11:00", "prerequisite": None}
    ]
    rooms = [{"name": "R1", "capacity": 30}]
    slots = ["Mon 09:00", "Mon 11:00"]
    availability = {"Alice": ["Mon 09:00", "Mon 11:00"]}
    result = generate_timetable(courses, rooms, slots, availability)
    assert result["timetable"][0]["slot"] == "Mon 11:00"


def test_scheduler_falls_back_when_preferred_slot_unavailable():
    courses = [
        {"code": "PRT582", "students": 25, "lecturer": "Alice",
         "preferred_slot": "Mon 11:00", "prerequisite": None}
    ]
    rooms = [{"name": "R1", "capacity": 30}]
    slots = ["Mon 09:00", "Mon 11:00"]
    availability = {"Alice": ["Mon 09:00"]}
    result = generate_timetable(courses, rooms, slots, availability)
    assert result["timetable"][0]["slot"] == "Mon 09:00"


def test_scheduler_prevents_room_clash():
    courses = [
        {"code": "A", "students": 20, "lecturer": "L1", "preferred_slot": "Mon 09:00", "prerequisite": None},
        {"code": "B", "students": 20, "lecturer": "L2", "preferred_slot": "Mon 09:00", "prerequisite": None},
    ]
    rooms = [{"name": "R1", "capacity": 30}]
    slots = ["Mon 09:00", "Mon 11:00"]
    availability = {"L1": slots, "L2": slots}
    result = generate_timetable(courses, rooms, slots, availability)
    assert result["timetable"][0]["slot"] != result["timetable"][1]["slot"]


def test_scheduler_prevents_lecturer_clash():
    courses = [
        {"code": "A", "students": 20, "lecturer": "L1", "preferred_slot": "Mon 09:00", "prerequisite": None},
        {"code": "B", "students": 20, "lecturer": "L1", "preferred_slot": "Mon 09:00", "prerequisite": None},
    ]
    rooms = [{"name": "R1", "capacity": 30}, {"name": "R2", "capacity": 30}]
    slots = ["Mon 09:00", "Mon 11:00"]
    availability = {"L1": slots}
    result = generate_timetable(courses, rooms, slots, availability)
    assert result["timetable"][0]["slot"] != result["timetable"][1]["slot"]


def test_scheduler_orders_prerequisite_before_dependent_course():
    courses = [
        {"code": "ADV", "students": 20, "lecturer": "L2", "preferred_slot": "Mon 11:00", "prerequisite": "BASIC"},
        {"code": "BASIC", "students": 20, "lecturer": "L1", "preferred_slot": "Mon 09:00", "prerequisite": None},
    ]
    rooms = [{"name": "R1", "capacity": 30}]
    slots = ["Mon 09:00", "Mon 11:00"]
    availability = {"L1": slots, "L2": slots}
    result = generate_timetable(courses, rooms, slots, availability)
    by_course = {x["course"]: x for x in result["timetable"]}
    assert slots.index(by_course["BASIC"]["slot"]) < slots.index(by_course["ADV"]["slot"])


def test_unschedulable_course_is_reported():
    courses = [
        {"code": "BIG", "students": 100, "lecturer": "L1", "preferred_slot": None, "prerequisite": None}
    ]
    rooms = [{"name": "R1", "capacity": 30}]
    slots = ["Mon 09:00"]
    availability = {"L1": ["Mon 09:00"]}
    result = generate_timetable(courses, rooms, slots, availability)
    assert result["timetable"] == []
    assert result["unscheduled"] == ["BIG"]


def test_same_inputs_produce_same_timetable():
    courses = [
        {"code": "A", "students": 20, "lecturer": "L1", "preferred_slot": None, "prerequisite": None}
    ]
    rooms = [{"name": "R1", "capacity": 30}]
    slots = ["Mon 09:00"]
    availability = {"L1": slots}
    assert generate_timetable(courses, rooms, slots, availability) == generate_timetable(
        courses, rooms, slots, availability
    )


# Invalid-input tests
@pytest.mark.parametrize("students", [0, -1])
def test_invalid_student_count_raises_value_error(students):
    with pytest.raises(ValueError):
        is_room_suitable({"students": students}, {"capacity": 30})


@pytest.mark.parametrize("capacity", [0, -1])
def test_invalid_room_capacity_raises_value_error(capacity):
    with pytest.raises(ValueError):
        is_room_suitable({"students": 20}, {"capacity": capacity})


def test_wrong_student_type_raises_type_error():
    with pytest.raises(TypeError):
        is_room_suitable({"students": "20"}, {"capacity": 30})


def test_missing_course_code_is_rejected():
    with pytest.raises(ValueError):
        validate_inputs(
            [{"students": 20, "lecturer": "L1", "prerequisite": None}],
            [{"name": "R1", "capacity": 30}],
            ["Mon 09:00"],
            {"L1": ["Mon 09:00"]},
        )


def test_missing_lecturer_is_rejected():
    with pytest.raises(ValueError):
        validate_inputs(
            [{"code": "A", "students": 20, "prerequisite": None}],
            [{"name": "R1", "capacity": 30}],
            ["Mon 09:00"],
            {},
        )


def test_unknown_availability_slot_is_rejected():
    with pytest.raises(ValueError):
        validate_inputs(
            [{"code": "A", "students": 20, "lecturer": "L1", "prerequisite": None}],
            [{"name": "R1", "capacity": 30}],
            ["Mon 09:00"],
            {"L1": ["Friday 99:00"]},
        )


def test_unknown_prerequisite_is_rejected():
    with pytest.raises(ValueError):
        validate_inputs(
            [{"code": "A", "students": 20, "lecturer": "L1", "prerequisite": "MISSING"}],
            [{"name": "R1", "capacity": 30}],
            ["Mon 09:00"],
            {"L1": ["Mon 09:00"]},
        )


def test_duplicate_course_codes_are_rejected():
    with pytest.raises(ValueError):
        validate_inputs(
            [
                {"code": "A", "students": 20, "lecturer": "L1", "prerequisite": None},
                {"code": "A", "students": 20, "lecturer": "L2", "prerequisite": None},
            ],
            [{"name": "R1", "capacity": 30}],
            ["Mon 09:00"],
            {"L1": ["Mon 09:00"], "L2": ["Mon 09:00"]},
        )


def test_cyclic_prerequisite_is_rejected():
    courses = [
        {"code": "A", "students": 10, "lecturer": "L1", "prerequisite": "B"},
        {"code": "B", "students": 10, "lecturer": "L2", "prerequisite": "A"},
    ]
    with pytest.raises(ValueError, match="cyclic"):
        generate_timetable(
            courses,
            [{"name": "R1", "capacity": 20}],
            ["Mon 09:00", "Mon 11:00"],
            {"L1": ["Mon 09:00"], "L2": ["Mon 11:00"]},
        )
