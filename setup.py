# -*-coding:utf-8 -*-
from setuptools import setup, find_packages
#requests
setup(
    name = "tupdate",
    description = "a update clinet ",
    version = "1.0",
    author = "shaochuyu",
    author_email = "shaochuyu@qq.com",
    install_requires = ["redis","eventlet","requests","pytz","pymongo"],
    packages=find_packages(),
    entry_points={
        "console_scripts":[
            'td01_install_pkt=tupdate.install_pkt:td01_install_pkt',
            'td01_make_pkt=tupdate.make_pkt:td01_make_pkt',
            
        ]
    }
)