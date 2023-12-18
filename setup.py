from setuptools import setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pyzabbix",
    version="1.3.1",
    description="Zabbix API Python interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Luke Cyca",
    author_email="me@lukecyca.com",
    license="LGPL",
    keywords="zabbix monitoring api",
    url="http://github.com/lukecyca/pyzabbix",
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: System :: Systems Administration",
    ],
    packages=["pyzabbix"],
    package_data={"": ["py.typed"]},
    python_requires=">=3.6",
    install_requires=[
        "requests>=1.0",
        "packaging",
    ],
    extras_require={
        "dev": [
            "black",
            "isort",
            "mypy",
            "pylint",
            "pytest-cov",
            "pytest-xdist",
            "pytest",
            "requests-mock",
            "types-requests",
        ],
    },
)
