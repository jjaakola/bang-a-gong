import setuptools

install_requires = [
    "kafka-python==2.0.2",
    "psycopg2-binary==2.8.6",
    "aiohttp==3.7.4.post0",
    "docopt==0.6.2",
    "PyYAML==5.4.1",
    "jsonpath-ng==1.5.2"
]

development_requirements = {
    "dev" : ["coverage==5.5",
             "pylint==2.8.2",
             "pycodestyle==2.7.0",
             "aioresponses==0.7.2",
             "docker-compose==1.29.1",
             "build==0.3.1.post1"]
}


setuptools.setup(
    name="api-status-monitor",
    version="0.0.1",
    author="jjaakola",
    description="Distributed API status monitor system.",
    url="https://github.com/jjaakola/bang-a-gong",
    project_urls={
        "Bug Tracker": "https://github.com/jjaakola/bang-a-gong/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Linux",
    ],
    entry_points = {
        'console_scripts': ['statusmonitor=api_status_monitor.statusmonitor:main'],
    },
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=install_requires,
    extras_require=development_requirements
)
