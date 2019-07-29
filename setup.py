import os
from setuptools import setup, find_packages

deps = {
    'lft': [
        "jsonrpcclient[requests,aiohttp]==3.3.3"
    ],
    'test': [
        "pytest==4.6.3",
        "pytest-asyncio==0.10.0"
    ],
}

deps['dev'] = deps['lft'] + deps['test']
install_requires = deps['lft']

setup(
    name='LFT',
    version='0.1.0',
    description='Loopchain Fault Tolerance',
    author='ICON Foundation',
    python_requires=">=3.6.5",
    install_requires=install_requires,
    extras_require=deps,
    license='Apache License 2.0',
    keywords='lft icon blockchain',
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6.5',
        'Programming Language :: Python :: 3.7'
    ],
    entry_points={
        'console_scripts': [
            'lft=lft.__main__:main',
        ],
    },
)
