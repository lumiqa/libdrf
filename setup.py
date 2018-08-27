import os
from setuptools import find_packages, setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='libdrf',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',
    description='Reusable apps and utilities for Django Rest Framework projects',
    url='https://github.com/lumiqa/libdrf',
    author='Adam Svanberg',
    author_email='adam@lumiqa.com',
    install_requires=[
        'djangorestframework>=3.8',
        'requests>=2',
        'PyJWT>=1.6.4',
    ]
)
