from setuptools import setup


setup(
    name='pronym-django-api',
    url='https://github.com/greggg230/pronym-django-api',
    author='Pronym',
    author_email='gregg@pronym.com',
    packages=['pronym_api'],
    install_requires=['Django>=2.4'],
    version='0.1',
    license='MIT',
    description=(
        'A thin wrapper around Django views for easily customized '
        'API endpoints.'),
    long_description=open('README.md').read(),
)
