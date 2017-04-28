from setuptools import setup, find_packages

version = '0.0'

classifiers = """
Development Status :: 4 - Beta
Environment :: Console
Intended Audience :: Developers
License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)
Operating System :: OS Independent
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
""".strip().splitlines()

long_description = (
    open('README.rst').read()
    + '\n' +
    open('CHANGES.rst').read()
    + '\n')

setup(
    name='repodono.jobs',
    version=version,
    description="Simple job server",
    long_description=long_description,
    classifiers=classifiers,
    keywords='',
    author='Tommy Yu',
    author_email='tommy.yu@auckland.ac.nz',
    url='https://github.com/repodono/repodono.jobs',
    license='gpl',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    extras_require={
        'sanic': [
            'sanic>=0.4',
        ],
        'dev': [
            'aiohttp',
        ],
    },
    namespace_packages=['repodono'],
    include_package_data=True,
    python_requires='>=3.4',
    zip_safe=False,
    install_requires=[
        'setuptools',
        # -*- Extra requirements: -*-
    ],
    entry_points="""
    # -*- Entry points: -*-
    """,
    test_suite="repodono.jobs.tests.make_suite",
)
