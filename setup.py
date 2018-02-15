from setuptools import setup, find_packages
import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(BASE_DIR, 'README.rst')) as f:
    README = f.read()

with open(os.path.join(BASE_DIR, 'requirements.txt')) as f:
    requirements = f.read().splitlines()

setup(name='cartpole-rl-remote',
      python_requires='>=3.5',
      version=__import__('cartpole').VERSION,
      description="Cartpole: Remote RL Agent",
      author_email=["engapa@gmail.com ", "davsuacar@gmail.com"],
      maintainer_email="engapa@gmail.com",
      license="Apache 2.0",
      long_description=README,
      classifiers=[
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Scientific/Engineering :: Artificial Intelligence',
          'Topic :: Scientific/Engineering :: Information Analysis'
      ],
      url='https://github.com/davsuacar/cartpole-rl-remote',
      packages=find_packages(exclude=["tests", "docs", "seldon", "proto"]),
      include_package_data=True,
      install_requires=requirements,
      entry_points={
          'console_scripts': [
              "cartpole = cartpole.client.cmd:main"
          ]
      },
      zip_safe=False)
