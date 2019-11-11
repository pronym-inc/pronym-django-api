from setuptools import find_packages, setup

install_dependencies = ['django==2.2.4', 'PyJWT==1.7.1']
test_dependencies = [
    'pytest-django==3.5.1', 'factory_boy==2.12.0', 'coverage==4.5.4',
    'pytest-cov==2.7.1']


setup(
    name='pronym_api',
    url='https://github.com/greggg230/pronym-django-api',
    author='Pronym',
    author_email='gregg@pronym.com',
    packages=find_packages(),
    install_requires=install_dependencies,
    tests_require=test_dependencies,
    extras_require={'test': test_dependencies},
    version='1.0.6',
    license='MIT',
    description=(
        'A thin wrapper around Django views for easily customized '
        'API endpoints.'),
    long_description=open('README.md').read(),
)
