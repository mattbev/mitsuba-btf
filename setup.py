"""
PyPI build file
"""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

base_reqs = [
    "btf-extractor", 
    "mitsuba", 
    "scipy", 
    "tqdm"
]

setuptools.setup(
    name="mitsuba-btf",
    version="0.1.0",
    author="Ryota Maeda",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=base_reqs,
    extras_require={},
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6, <3.10",
)
