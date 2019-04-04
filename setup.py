# -*-coding:utf-8 -*-
from setuptools import setup, find_packages
#requests
setup(
    name = "tupdate",
    description = "a update clinet ",
    version = "1.0",
    author = "shaochuyu",
    author_email = "shaochuyu@qq.com",
    install_requires = [""],
    packages=find_packages(),
    entry_points={
        "console_scripts":[
            'td01_make_pkt=tupdate.make_pkt:td01_make_pkt',
            'tupdate_deamon=tupdate.app:tupdate_deamon'
        ]
    }
)