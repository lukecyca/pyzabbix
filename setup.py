from setuptools import setup

with open("README.markdown", "r") as fh:
    long_description = fh.read()

setup(
    name="pyzabbix",
    version="1.0.0",
    install_requires=[
        "requests>=1.0",
        "semantic-version>=2.8"
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
        "Programming Language :: Python :: 2.7",
	"Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
	"Programming Language :: Python :: 3.6",
	"Programming Language :: Python :: 3.7",
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
