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
        for variant in ("exact", "local", "domain", "mixed", "unicode-expansion")
    },
    **{
        f"test_student_details_4[{variant}]": "student-details-4"
        for variant in ("tag", "domain", "spaces", "unicode-composition")
    },
    "test_student_details_5": "student-details-5",
    "test_student_details_6": "student-details-6",
    "test_student_details_7": "student-details-7",
    "test_student_details_8": "student-details-8",
    "test_student_details_9": "student-details-9",
    "test_student_details_10": "student-details-10",
}


ENROLLMENT_CASES = {
    **{
        f"test_scenario[{number}-{outcome}]": f"enrollment-{number}"
        for number, outcome in enumerate(
            (
                "SUCCESS",
                "SUCCESS",
                "COURSE_NOT_OFFERED",
                "MISSING_STUDENT",
                "MISSING_PROGRAMME",
                "MISSING_COURSE",
                "COURSE_NOT_OFFERED",
                "ALREADY_ENROLLED",
                "ALREADY_ENROLLED",
                "SUCCESS",
                "PERSISTENCE_FAILURE",
                "ALREADY_ENROLLED",
                "DENIED",
                "DENIED",
                "COURSE_NOT_OFFERED",
            ),
            1,
        )
    },
    **{
        f"test_enrollment_16_factory_failure_after_insert[{fault}]": "enrollment-16"
        for fault in ("rejection", "exception")
    },
    "test_enrollment_17_definite_commit_failure": "enrollment-17",
    "test_enrollment_18_restore_historical_pair": "enrollment-18",
    **{
        f"test_enrollment_19_invalid_course_precedes_lookup[{token}-{expected}-{missing}]": "enrollment-19"
        for missing in ("student", "programme")
        for token, expected in (
            ("s", "INVALID_REQUEST"),
            ("other", "DENIED"),
            ("invalid", "DENIED"),
        )
    },
}

STUDENT_CASES.update(
    {
        "test_student_details_11": "student-details-11",
        **{
            f"test_student_details_12[{fault}]": "student-details-12"
            for fault in ("rejection", "exception", "commit")
        },
        "test_student_details_13": "student-details-13",
        "test_student_details_14": "student-details-14",
        "test_student_details_15": "student-details-15",
        **{
            f"test_student_details_16[{value}]": "student-details-16"
            for value in (
                "None",
                "True",
                "False",
                "1",
                "1.0",
                "0",
                "-1",
                "9223372036854775808",
            )
        },
        **{
            f"test_student_details_17[{loss}]": "student-details-17"
            for loss in ("response", "uncertain")
        },
    }
)
