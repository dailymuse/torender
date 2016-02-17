from setuptools import setup

version = "0.1.0"

setup(
    name = "torender",
    version = version,
    description = "A prerender middleware for the tornado web framework",
    author = "Yusuf Simonson",
    author_email = 'yusuf@themuse.com',
    url = "http://github.com/dailymuse/oz",
    zip_safe = False,
    
    packages = [
        "torender"
    ],

    package_data = {
        "oz": [
            "skeleton/*.py",
            "skeleton/plugin/*.py",
            "skeleton/plugin/tests/*.py",
        ]
    },

    install_requires = [
        "tornado>=3.1",
    ],
)
