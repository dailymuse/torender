from setuptools import setup

version = "0.2.0"

setup(
    name = "torender",
    version = version,
    description = "A prerender middleware for the tornado web framework",
    author = "Yusuf Simonson",
    author_email = 'yusuf@themuse.com',
    url = "http://github.com/dailymuse/torender",
    zip_safe = False,
    
    packages = [
        "torender"
    ],

    install_requires = [
        "tornado>=3.1",
    ],
)
