from distutils.core import setup

setup(
    name="pyzabbix",
    version="0.1",
    description="Zabbix API Python interface",
    author="Luke Cyca",
    author_email="me@lukecyca.com",
    license = "LGPL",
    keywords = "zabbix monitoring api",
    url = "http://github.com/lukecyca/pyzabbix",
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
        "Topic :: System :: Systems Administration",
    ],

    packages=["pyzabbix"],
)