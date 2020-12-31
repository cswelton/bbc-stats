import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bbc_stats",
    version="1.0.0",
    author="Craig Welton",
    description="Syncs round data and builds statistics and data files for zogby-group website",
    install_requires=[
        'numpy>=1.19.4',
        'terminaltables==3.1.0',
        'XlsxWriter==1.3.7',
        'pyyaml==5.3.1',
        'golfgenius @ git+https://github.com/cswelton/golfgenius@master'
    ],
    entry_points={
        "console_scripts": [
            'bbc-stats=bbc_stats.generate:main',
            'bbc-sync=bbc_stats.sync_golfgenius:main'
        ],
    },
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cswelton/bbc-stats/bbc_stats",
    packages=['bbc_stats'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    license='MIT',
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=['nose'],
    zip_safe=False)
