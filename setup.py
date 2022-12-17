from pathlib import Path

from setuptools import find_packages, setup

setup(
    name="todonotifier",
    description="Library to setup automatic TODO Notifications in code",
    long_description=Path("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/ashu-tosh-kumar/todo_notifier",
    author="Ashutosh Kumar",
    download_url="https://pypi.org/project/todonotifier/",
    license="MIT",
    test_suite="unittest",
    version="1.2.2",
    keywords=["todo", "notifier"],
    packages=find_packages(exclude=["tests", "sample_reports"]),
    install_requires=[
        "GitPython==3.1.29",
        "python-dateutil==2.8.2",
    ],
)
