from setuptools import setup, find_packages

setup(
    name="django-extensible-models",
    version="0.1",
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    license="MIT",
    description="A Django app to create extensible models with per-tenant schemas.",
    long_description=open("README.org").read(),
    install_requires=[
        "Django>=4.2",
        "jsonschema>=4.21.0",
        "djangorestframework>=3.14.0",
    ],
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
)
