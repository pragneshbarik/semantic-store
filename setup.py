import os
import pkg_resources
from setuptools import setup, find_packages

requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")

if os.path.isfile(requirements_path):
    with open(requirements_path) as f:
        requirements = [str(r) for r in pkg_resources.parse_requirements(f)]
else:
    requirements = []

setup(
    name="semantic-store",
    version="0.0.2",
    description="An in-memory vector store for semantic data storage and retrieval",
    author="Pragnesh Barik",
    packages=find_packages(exclude=["tests*"]),
    keywords=['in-memory', 'vector', 'database', 'semantic', 'search'],
    install_requires=requirements,
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    package_dir={'': 'src'},
    include_package_data=True,

)
