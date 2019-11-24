from codecs import open
import os
import re
import sys
from setuptools import setup


PY_VER = sys.version_info


if PY_VER < (3, 6):
    raise RuntimeError("aioch doesn't suppport Python earlier than 3.6")


here = os.path.abspath(os.path.dirname(__file__))


def read_version():
    regexp = re.compile(r'^VERSION\W*=\W*\(([^\(\)]*)\)')
    init_py = os.path.join(here, 'aioch', '__init__.py')
    with open(init_py) as f:
        for line in f:
            match = regexp.match(line)
            if match is not None:
                return match.group(1).replace(', ', '.')
        else:
            raise RuntimeError('Cannot find version in aioch/__init__.py')


with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='aioch',
    version=read_version(),

    description=(
        'Library for accessing a ClickHouse database over native interface '
        'from the asyncio'
    ),
    long_description=long_description,
    long_description_content_type='text/markdown',

    url='https://github.com/mymarilyn/aioch',

    author='Konstantin Lebedev',
    author_email='kostyan.lebedev@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 4 - Beta',


        'Environment :: Console',

        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',


        'License :: OSI Approved :: MIT License',


        'Operating System :: OS Independent',


        'Programming Language :: SQL',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',

        'Topic :: Database',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Information Analysis'
    ],

    keywords='ClickHouse db database cloud analytics asyncio',

    packages=['aioch'],
    install_requires=[
        'clickhouse-driver>=0.1.2'
    ],
    test_suite='nose.collector',
    tests_require=[
        'nose'
    ],
)
