from setuptools import setup

setup(
    name="datetaken",
    version="0.1.0",
    author="David Minnerly",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.4",
    ],
    keywords="photo rename date datetaken",
    py_modules=["rename"],
    install_requires=[
        "docopt",
        "piexif"
    ],
    entry_points={
        "console_scripts": [ "datetaken=rename:main" ]
    }
)
