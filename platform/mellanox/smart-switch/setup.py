from setuptools import setup

setup(
    name='mlnx-platform-api-dpuctl',
    version='1.0',
    description='SONiC platform API wrapper for reset flows',
    license='Apache 2.0',
    author='SONiC Team',
    author_email='',
    url='',
    maintainer='',
    maintainer_email='',
    packages=[
        'dpuctl',
        'tests'
    ],
    setup_requires=[
        'pytest-runner'
    ],
    install_requires=[
        'inotify',
    ],
    tests_require=[
        'pytest',
        'mock>=2.0.0'
    ],
    entry_points={
        'console_scripts': [
                            'dpuctl = dpuctl.main:dpuctl',
                            ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.9',
        'Topic :: Platform api wrapper',
    ],
    keywords='Sonic platform ',
)
