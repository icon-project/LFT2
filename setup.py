import os
from setuptools import setup, find_packages

version = os.environ.get('VERSION')

if version is None:
    with open(os.path.join('.', 'VERSION')) as version_file:
        version = version_file.read().strip()

deps = {
    'lft': [
        "jsonrpcclient[requests,aiohttp]==3.3.5"
    ],
    'app': [
        "coloredlogs==10.0",
        "ipython==7.9.0"
    ],
    'test': [
        "mock==4.0.1",
        "pytest==4.6.3",
        "pytest-asyncio==0.10.0"
    ],
}

deps['app'] = deps['lft'] + deps['app']
deps['dev'] = deps['test'] = deps['app'] + deps['test']
install_requires = deps['lft']

setup(
    name='LFT',
    version=version,
    description='Loopchain Fault Tolerance',
    long_description_content_type='text/markdown',
    long_description=open('README.md').read(),
    url='https://github.com/icon-project/lft2',
    author='ICON Foundation',
    author_email='foo@icon.foundation',
    python_requires=">=3.7.0",
    install_requires=install_requires,
    extras_require=deps,
    license='Apache License 2.0',
    keywords='lft icon blockchain',
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.7'
    ],
    entry_points={
        'console_scripts': [
            'lft=lft.__main__:main',
        ],
    },
)
