from enum import StrEnum


class StudentResult(StrEnum):
    ALREADY_EXISTS = "STUDENT_ALREADY_EXISTS"
    NOT_FOUND = "STUDENT_NOT_FOUND"
    STORAGE_FAILURE = "STUDENT_STORAGE_FAILURE"


class StudentWrite(StrEnum):
    SAVED = "SAVED"
    EMAIL_KEY_CONFLICT = "EMAIL_KEY_CONFLICT"


Saved = StudentWrite.SAVED
EmailKeyConflict = StudentWrite.EMAIL_KEY_CONFLICT
