DEFAULT_EXCLUDE_DIRS = {
    "PATTERN": ["*.egg-info/"],  # Distribution / packaging
    "NAME": [
        "__pycache__",
        ".env",  # Environments
        ".venv",  # Environments
        "env",  # Environments
        "venv",  # Environments
        "ENV",  # Environments
        "env.bak",  # Environments
        "venv.bak",  # Environments
        ".history",  # VS Code
        ".local",  # local user folder
        ".vscode",  # VS Code
        "build",  # Distribution / packaging
        "develop-eggs",  # Distribution / packaging
        "dist",  # Distribution / packaging
        "downloads",  # Distribution / packaging
        "lib",  # Distribution / packaging
        "lib64",  # Distribution / packaging
        "parts",  # Distribution / packaging
        "sdist",  # Distribution / packaging
        "var",  # Distribution / packaging
        "wheels",  # Distribution / packaging
        "pip-wheel-metadata",  # Distribution / packaging
        "share/python-wheels",  # Distribution / packaging
        "htmlcov",  # Unit test / coverage reports
        ".tox",  # Unit test / coverage reports
        ".nox",  # Unit test / coverage reports
        "*.cover",  # Unit test / coverage reports
        "*.py,cover",  # Unit test / coverage reports
        ".hypothesis",  # Unit test / coverage reports
        ".pytest_cache",  # Unit test / coverage reports
        "instance",  # Flask stuff
        "_build",  # Sphinx documentation
        "target",  # PyBuilder
        "profile_default",  # IPython
        "__pypackages__",  # PEP 582; used by e.g. github.com/David-OConnor/pyflow
        "site",  # mkdocs documentation
        ".mypy_cache",  # mypy
        ".pyre",  # Pyre type checker
    ],
    "ABS_PATH": [],
}

DEFAULT_EXCLUDE_FILES = {
    "PATTERN": [
        "*.py[cod]",  # Byte-compiled / optimized / DLL files
        "*$py.class",  # Byte-compiled / optimized / DLL files
        "*.so",  # C extensions
        "*.manifest",  # PyInstaller
        "*.spec",  # PyInstaller
        ".coverage.*",  # Unit test / coverage reports
        ".cache",  # Unit test / coverage reports
        "nosetests.xml",  # Unit test / coverage reports
        "coverage.xml",  # Unit test / coverage reports
        "*.mo",  # Translations
        "*.pot",  # Translations
        "*.log",  # Django stuff
        "*.sage.py",  # SageMath parsed files
    ],
    "NAME": [
        ".coverage",  # Unit test / coverage reports
        "pip-log.txt",  # Installer logs
        "pip-delete-this-directory.txt",  # Installer logs
        "local_settings.py",  # Django stuff:
        "db.sqlite3",  # Django stuff:
        "db.sqlite3-journal",  # Django stuff
        ".webassets-cache",  # Flask stuff
        ".scrapy",  # Scrapy stuff
        ".ipynb_checkpoints",  # Jupyter Notebook
        "ipython_config.py",  # IPython
        ".python-version",  # pyenv
        "celerybeat-schedule",  # Celery stuff
        "celerybeat.pid",  # Celery stuff
        ".spyderproject",  # Spyder project settings
        ".spyproject",  # Spyder project settings
        ".ropeproject",  # Rope project settings
        ".dmypy.json",  # mypy
        "dmypy.json",  # mypy
    ],
    "ABS_PATH": [],
}

UNKNOWN_USER_NAME = "JANE_DOE"


class DEFAULT_SUMMARY_GENERATORS_ENUM:
    EXPIRED_TODO_BY_USER = "Expired TODO Items"
    TODO_BY_MODULE = "Module-wise Summary"
    UPCOMING_TODO_BY_USER = "Upcoming Week TODO Items"
