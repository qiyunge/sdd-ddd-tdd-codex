from enum import StrEnum


class Rejection(StrEnum):
    DENIED = "DENIED"
    ALREADY_ENROLLED = "ALREADY_ENROLLED"
    COURSE_NOT_OFFERED = "COURSE_NOT_OFFERED"
