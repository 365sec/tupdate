# !/usr/bin/python
#coding:utf-8
import os
from  tupdate import pkt_key
from  tupdate.utils import rc4Decrypt,un_zip
import sqlite3
import codecs
import datetime
import json




def return_output(data):   
    print json.dumps(data,ensure_ascii=False)
    
    
def td01_install_pkt(update_file,updateinfo,updateversion,updatetype):
    updatestatus=""
    if update_file == None  :
       return 
    try:
        os.system("rm -rf /td01/tupdate/*")
        rc4Decrypt(update_file,update_file,pkt_key)
        un_zip(update_file,"/td01/tupdate")
        os.system("cd /td01/tupdate/ && chmod +x update.sh && ./update.sh 2>&1 >/dev/null")
        return_output({"td01_install_pkt":"ok"})
        updatestatus = "ok"

    except Exception as e:
        return_output({"td01_install_pkt":str(e)})
    try:
        describe_content = None
        if updateinfo != None:
            with codecs.open(updateinfo, 'rb', 'utf-8') as f:
                describe_content = f.read()
                describe_content = describe_content.replace("\'", "")
        update_version = ""
        update_info = ""
        update_status = "false"
        status_file = "/td01/status.json"
        status = {}
        try:
            fp = open(status_file, "rb")
            status = json.load(fp)
            fp.close()
        except Exception as e:
            update_status = "false"
            status = {"poc_version": "20190100", "code_version": "1.1.1", "rule_version": "20190100",
                      "upgrade_url": "http://172.16.39.230:8100"}
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
        fp = open(status_file, "wb")
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
        os.system("rm -rf /td01/tupdate/*")
    except Exception as e:
        pass