import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="engin",
    version="0.1.992",
    author="Alexandr A",
    author_email="flo0.webmaster@gmail.com",
    description="A set of tools to develop web scrapers",
    url="https://github.com/flo0web/engin",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
