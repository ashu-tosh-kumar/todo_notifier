from summary_generators import (ExpiredTodosByUser, SummaryByModule,
                                UpcomingWeekTodosByUser)

DEFAULT_EXCLUDE_DIRS = {
    "PATTERN": [
        ".*"
    ],
    "NAME": [],
    "ABS_PATH": []
}

DEFAULT_EXCLUDE_FILES = {
    "PATTERN": [
        ".*"
    ],
    "NAME": [],
    "ABS_PATH": []
}

UNKNOWN_USER_NAME = "JANE_DOE"

DEFAULT_SUMMARY_GENERATORS = [
    ExpiredTodosByUser("Expired TODO Items"),
    SummaryByModule("Module-wise Summary"),
    UpcomingWeekTodosByUser("Upcoming Week TODO Items")
]
