from setuptools import setup


setup(
    name='v4l2-cffi',
    version='0.1',
    description='Python binding for V4L2 API',
    author='geehalel',
    author_email='geehalel@gmail.com',
    #packages=['v4l2'],
    py_modules=['v4l2', 'v4l2enums'],
    include_package_data=False,
    install_requires=['cffi>=1.10'],
    setup_requires=['cffi>=1.10', 'pycparserext'],
    url='https://github.com/geehalel/v4l2-cffi',
    keywords='Video, V4L2, cffi',
    classifiers=[
	"Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
	"License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: POSIX :: Linux",
        "Natural Language :: English",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    cffi_modules=["v4l2_build.py:maker"]
)
