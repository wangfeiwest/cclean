from setuptools import setup, find_packages

setup(
    name="cclean-python",
    version="1.0.0",
    description="Windows C Drive Cleaner Tool - Python Version",
    author="CClean Development Team",
    author_email="",
    packages=find_packages(),
    install_requires=[
        "pywin32>=306",
        "colorama>=0.4.4", 
        "tqdm>=4.64.0",
        "psutil>=5.9.0"
    ],
    entry_points={
        'console_scripts': [
            'cclean-py=cclean.main:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
)