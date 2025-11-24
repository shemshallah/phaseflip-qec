# 📄 FILE 1: setup.py

**Filename:** `setup.py`  
**Purpose:** Python package installation configuration  
**Location:** Root directory

```python
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="phaseflip-qec",
    version="1.0.0",
    author="OaGI Research",
    author_email="[your email here]",
    description="Million-fold quantum error suppression for phase errors",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/oagi-research/phaseflip-qec",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "qiskit>=0.45.0",
        "qiskit-aer>=0.13.0",
        "numpy>=1.23.0",
        "scipy>=1.10.0",
        "matplotlib>=3.7.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "black>=23.0", "pylint>=2.17"],
        "docs": ["sphinx>=6.0", "sphinx-rtd-theme>=1.2"],
    },
)