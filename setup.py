import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="engin",
    version="2.0",
    author="Alexandr A",
    author_email="flo0.webmaster@gmail.com",
    description="A set of tools to develop web scrapers",
    url="https://github.com/flo0web/engin",
    install_requires=[
        'aiohttp', 'lxml', 'cssselect'
    ],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
