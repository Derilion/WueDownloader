import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="MoodleDownloader",
    version="1.0",
    author="Derilion",
    author_email="derilion@example.com",
    description="A small script to download current course files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Derilion/WueDownloader",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Linux",
    ],
    python_requires='>=3.7',
)
