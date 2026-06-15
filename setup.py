from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="slbom",
    version="1.0.0",
    description="Custom BOM and Costing Module",
    author="rajgills.it@gmail.com",
    author_email="rajgills.it@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
