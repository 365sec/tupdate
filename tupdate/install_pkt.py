# !/usr/bin/python
#coding:utf-8
import os
import sqlite3
import codecs
import datetime
import json

from  tupdate import pkt_key
from  tupdate.config import STATUS_FILE_PATH,UPDATE_INFO_FILE
from  tupdate.utils import rc4Decrypt,un_zip


def td01_install_pkt(update_file,updateversion,updatetype):
    updatestatus=""
    update_version = ""
    update_info = ""
    update_status = "false"
    updatestatus = "ok"
    describe_content = None
    status = {}
    if update_file == None  :
       return 
   
    try:
        os.system("rm -rf /td01/tupdate/*")
        rc4Decrypt(update_file,update_file,pkt_key)
        un_zip(update_file,"/td01/tupdate")
        os.system("cd /td01/tupdate/ && chmod +x update.sh && ./update.sh 2>&1 >/dev/null")
     
        try:
            with codecs.open(UPDATE_INFO_FILE, 'rb', 'utf-8') as f:
                    describe_content = f.read()
                    describe_content = describe_content.replace("\'", "")
        except :
            pass
            
        try:
            fp = open(STATUS_FILE_PATH, "rb")
            status = json.load(fp)
            fp.close()
        except Exception as e:
            update_status = "false"
            status = {"poc_version": "20190100", "code_version": "1.1.1", "rule_version": "20190100",
                      "upgrade_url": "http://tscanv.com:48100"}
            
        if updateversion != None and updatetype != None:
            if updatetype == "1":
                update_info = "代码更新"
                status["code_version"] = updateversion
                update_version = "代码-" + updateversion
            elif updatetype == "2":
                update_info = "漏洞库更新"
                status["poc_version"] = updateversion
                status["rule_version"] = updateversion
                update_version = "漏洞库-" + updateversion
        else:
            print "args.update_version != None  and args.update_type != None"
            return
        fp = open(STATUS_FILE_PATH, "wb")
        fp.write(json.dumps(status))
        fp.close()
        if updatestatus == "ok":
            update_status = "true"
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect('/td01/update.db')
        c = conn.cursor()
        datas = (update_version, update_info, time, '', 'true', describe_content)
        conn.text_factory = str
        c.execute("insert into t_update(version_num,instruction,time,use_time,state,describe) values(?,?,?,?,?,?)",
                  (datas));
        conn.commit()
        conn.close()
    except Exception as e:
        return  
    finally:
        os.system("rm -rf /td01/tupdate/*")
        
