import os
from codecs import open
from setuptools import find_packages, setup

import pyangbind


# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open("requirements.txt", "r") as fp:
    reqs = [r for r in fp.read().splitlines() if (len(r) > 0 and not r.startswith("#"))]

with open("README.rst") as readme:
    long_description = readme.read()


setup(
    name="pyangbind",
    # PyangBind uses the same versioning approach as OpenConfig - see
    # http://www.openconfig.net/file-cabinet/Semantic_Versioning_for_OpenConfig.pdf?attredirects=0&d=1
    version=pyangbind.__version__,
    description="PyangBind is a plugin for pyang which converts YANG data"
    + "models into a Python class hierarchy, such that Python "
    + "can be used to manipulate data that conforms with a YANG"
    + " model.",
    long_description=long_description,
    url="https://github.com/robshakir/pyangbind",
    author="Rob Shakir",
    author_email="rjs@rob.sh",
    license="Apache",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Telecommunications Industry",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
    ],
    include_package_data=True,
    keywords="yang pyang",
    packages=find_packages(exclude=["tests.*", "tests"]),
    install_requires=reqs,
    zip_safe=False,
    test_suite="tests.test_suite",
)
