from summary_generators import (
    ExpiredTodosByUser,
    SummaryByModule,
    UpcomingWeekTodosByUser,
)

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


class DEFAULT_SUMMARY_GENERATORS_ENUM:
    EXPIRED_TODO_BY_USER = "Expired TODO Items"
    TODO_BY_MODULE = "Module-wise Summary"
    UPCOMING_TODO_BY_USER = "Upcoming Week TODO Items"
<<<<<<< HEAD


DEFAULT_SUMMARY_GENERATORS = [
    ExpiredTodosByUser(DEFAULT_SUMMARY_GENERATORS_ENUM.EXPIRED_TODO_BY_USER),
    SummaryByModule(DEFAULT_SUMMARY_GENERATORS_ENUM.TODO_BY_MODULE),
    UpcomingWeekTodosByUser(DEFAULT_SUMMARY_GENERATORS_ENUM.UPCOMING_TODO_BY_USER)
]
