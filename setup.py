"""Setup script for django-swallow"""
from setuptools import setup
from setuptools import find_packages


setup(
    name='django-swallow',
    version='0.1',
    packages=find_packages(exclude=['test', 'tests',
                                    'example',]),
    include_package_data=True,
    license='BSD License',
    description='Make your django project able to import XMLs '
    'in an easily configurable way.',
    long_description=open('README.rst').read(),
    author='Djaz Team',
    author_email='devweb@liberation.fr',
    url='http://www.liberation.fr/',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ])
