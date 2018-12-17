from setuptools import setup




setup(name='markingpy',
      author='InAKleinBottle',
      email='admin@inakleinbottle.com',
      version='1.0.0',
      packages=['markingpy'],
      install_requires=['pylint'],
      test_suite='tests',
      #scripts = ['bin/markingpy'],
      entry_points = {
          'console_scripts' : ['markingpy=markingpy.cli:main'],
          },
      package_data = {'markingpy' : ['data/markingpy.conf']}
      )
