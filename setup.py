from setuptools import setup, find_packages

setup(
    name='pyannoyer',
    version='1.0.0',
    install_requires=[],
    packages=find_packages(where='src'),
    package_dir={
        'pyannoyer': 'src/pyannoyer'
    },
    description='pyannoyer will annoy you!',
    author='Wei-Fan Chiang',
    author_email='weifan.wf@gmail.com',
    license='BSD',
    zip_safe=True)