from setuptools import setup, find_packages

setup(
    name="potion-lang",
    version="0.1.0",
    description="Potion Language Compiler",
    author="Willians Costa da Silva",
    author_email="willianscsilva@gmail.com",
    packages=find_packages(),  # Encontra cli, lexer, parser, etc.
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "potionc=cli.potionc:main",  # Executável 'potionc' chamará cli/potionc.py:main()
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires='>=3.7',
)
