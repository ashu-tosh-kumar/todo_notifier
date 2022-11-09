from pathlib import Path

from setuptools import find_packages, setup

setup(
    name="todo_notifier",
    description="Library to setup automatic TODO Notifications in code",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/gmyrianthous/example-publish-pypi",
    author="Ashutosh Kumar",
    download_url="",  # To add later
    license="MIT",
    test_suite="unittest",
    version="1.1.0",
    keywords=["todo", "notifier"],
    packages=find_packages(exclude=["test"]),
    install_requires=[
        "GitPython==3.1.29",
        "python-dateutil==2.8.2",
    ],
)
