#!/usr/bin/python3

import setuptools

kwargs = {
    "name":         "zpool-status",
    "version":      "0.1",
    "author":       "Lars Gustäbel",
    "author_email": "lars@gustaebel.de",
    "url":          "https://github.com/gustaebel/zpool-status/",
    "description":  "Parse output from zpool status",
    "license":      "BSD",
    "classifiers":  ["Development Status :: 3 - Alpha",
                     "Environment :: Console",
                     "Intended Audience :: Developers",
                     "Intended Audience :: System Administrators",
                     "License :: OSI Approved :: BSD License",
                     "Operating System :: POSIX",
                     "Operating System :: POSIX :: Linux",
                     "Topic :: File Formats :: JSON",
                     "Topic :: Software Development :: Libraries :: Python Modules",
                     "Topic :: System :: Filesystems",
                     "Topic :: Utilities",
                     "Programming Language :: Python :: 3"],
    "python_requires": ">=3.7",
    "py_modules":   ["zpool_status"]
}

setuptools.setup(**kwargs)
