from setuptools import setup

with open("README.markdown", "r") as fh:
    long_description = fh.read()

setup(
    name="pyzabbix",
    version="0.8.1",
    install_requires=[
        "requests>=1.0",
    ],
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
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: System :: Systems Administration",
    ],
    packages=["pyzabbix"],
    tests_require=[
        "httpretty<0.8.7",
    ],
)
