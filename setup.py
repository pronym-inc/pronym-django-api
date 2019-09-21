from setuptools import find_packages, setup


setup(
    name='pronym_django',
    url='https://github.com/greggg230/pronym-django-api',
    author='Pronym',
    author_email='gregg@pronym.com',
    packages=find_packages(),
    install_requires=['django==2.2.4', 'django-nose==1.4.6', 'PyJWT==1.7.1'],
    version='0.1',
    license='MIT',
    description=(
        'A thin wrapper around Django views for easily customized '
        'API endpoints.'),
    long_description=open('README.md').read(),
)
