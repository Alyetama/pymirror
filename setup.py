from setuptools import setup
  

with open('requirements.txt') as f:
    requirements = f.readlines()
  
long_description = 'Upload files to multiple free hosting servers'
  
setup(
        name ='pymirror',
        version ='0.1.6',
        author ='Alyetama',
        url ='https://github.com/Alyetama/pymirror',
        description ='Upload files to multiple free hosting servers',
        long_description = long_description,
        long_description_content_type ="text/markdown",
        license ='MIT',
        packages = ['pymirror'],
        entry_points ={
            'console_scripts': [
                'pymirror = pymirror.pymirror:main'
            ]
        },
        classifiers =(
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ),
        keywords ='mirror upload files hosting',
        install_requires = requirements,
        zip_safe = False
)
