"""Approved mandatory Student-details variants, independent of test collection counts."""

STUDENT_CASES = {
    "test_student_details_1": "student-details-1",
    **{
        f"test_student_details_2[{value}-{field}]": "student-details-2"
        for value in ("missing", "nontext", "empty", "whitespace", "unicode")
        for field in ("name", "email")
    },
    **{
        f"test_student_details_3[{variant}]": "student-details-3"
        for variant in ("exact", "local", "domain", "mixed")
    },
    **{
        f"test_student_details_4[{variant}]": "student-details-4"
        for variant in ("tag", "domain", "spaces")
    },
    "test_student_details_5": "student-details-5",
    "test_student_details_6": "student-details-6",
    "test_student_details_7": "student-details-7",
}
