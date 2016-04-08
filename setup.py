from setuptools import setup, find_packages
from pip.req import parse_requirements
from codecs import open
from os import path

thisdir = path.abspath(path.dirname(__file__))
pip_reqs = parse_requirements(path.join(thisdir, "requirements.txt"), session=False)
inst_reqs = [str(ir.req) for ir in pip_reqs]

import pyangbind

with open(path.join(thisdir, "README.rst"), encoding='utf-8') as readme:
  long_description = readme.read()

setup(
    name='pyangbind',

    # PyangBind uses the same versioning approach as OpenConfig - see
    # http://www.openconfig.net/file-cabinet/Semantic_Versioning_for_OpenConfig.pdf?attredirects=0&d=1
    version=pyangbind.__version__,

    description="PyangBind is a plugin for pyang which converts YANG data" + \
                "models into a Python class hierarchy, such that Python " +  \
                "can be used to manipulate data that conforms with a YANG" + \
                " model.",
    long_description=long_description,

    url="https://github.com/robshakir/pyangbind",

    author="Rob Shakir",
    author_email="rjs@rob.sh",

    license="Apache",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Telecommunications Industry',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Code Generators',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only'
    ],
    include_package_data=True,
    keywords="yang pyang",
    packages=find_packages(exclude=['lib']),
    install_requires=inst_reqs,
    zip_safe = False,
)
