import os
import pkg_resources
from setuptools import setup, find_packages




setup(
    name="semantic-store",
    version="0.0.9",
    description="An embedded vector store for semantic data storage and retrieval",
    author="Pragnesh Barik",
    packages=find_packages(),
    keywords=['embedded database', 'vector', 'database', 'semantic', 'search'],
    install_requires=[
        str(r)
        for r in pkg_resources.parse_requirements(
            open(os.path.join(os.path.dirname(__file__), "requirements.txt"))
        )
    ],
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    include_package_data=True,
)
