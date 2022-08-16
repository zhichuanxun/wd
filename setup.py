import setuptools

with open('./README.md', 'r') as f:
    description = f.read()

setuptools.setup(
    name="words",
    long_description=description,
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'wd=src.wd:main'
        ]
    }
)