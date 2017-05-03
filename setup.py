import codecs

from os.path import abspath, dirname, join

from setuptools import find_packages, setup

from pip.req import parse_requirements


here = abspath(dirname(__file__))


PACKAGE_VERSION = '0.1.1'

with codecs.open(join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

install_reqs = parse_requirements(join(here, 'requirements.txt'), session=False)
# reqs = [str(ir.req) for ir in install_reqs]
reqs = install_reqs

setup(
    name='box-connector',
    version=PACKAGE_VERSION,
    author='APAC PS team',
    author_email='alinovskiy@odin.com',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    setup_requires=['nose>=1.0'],
    install_requires=reqs,
    url='https://github.com/odin-public/',
    license='Apache License',
    description='A sample connector for FallBall file sharing application',
    long_description=long_description,
)
