from setuptools import setup, find_packages
import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(BASE_DIR, 'README.rst')) as f:
    README = f.read()

with open(os.path.join(BASE_DIR, 'requirements.txt')) as f:
    requirements = f.read().splitlines()

setup(name='cartpole-rl-remote',
      python_requires='>=3.5',
      version="1.0.0",
      description="Cartpole: Remote RL Agent",
      author_email=["engapa@gmail.com ", "davsuacar@gmail.com"],
      maintainer_email="engapa@gmail.com",
      license="MIT",
      long_description=README,
      classifiers=[
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Scientific/Engineering :: Artificial Intelligence',
          'Topic :: Scientific/Engineering :: Information Analysis',
          'License :: OSI Approved :: MIT License',
      ],
      url='https://github.com/hypnosapos/cartpole-rl-remote',
      packages=find_packages(exclude=["tests", "docs", "seldon"]),
      include_package_data=True,
      install_requires=requirements,
      entry_points={
          'console_scripts': [
              "cartpole = cartpole.client.shell_cmd:main"
          ]
      },
      zip_safe=False)
