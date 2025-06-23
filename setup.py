from setuptools import setup

setup(
    name='hello_world',
    version='1.0.0',
    description='A simple hello world package',
    py_modules=['hello_world'],
    entry_points={
        'console_scripts': [
            'hello-world=hello_world:hello_world',
        ],
    },
    author='Your Name',
    author_email='your.email@example.com',
    license='Public Domain',
    python_requires='>=3.6',
)