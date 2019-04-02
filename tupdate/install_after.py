#coding:utf8
import sqlite3
import codecs
import datetime
import json
import argparse
import os

"""
#1-code  #2-po
#ok-升级成功  fail-升级失败
"""

def return_output(data):
    print json.dumps(data,ensure_ascii=False)

def td01_install_after(update_info,update_version,update_type,update_status,after_sh):
    describe_content=None
    if update_info != None  :
        with codecs.open(update_info, 'rb', 'utf-8') as f:
            describe_content = f.read()
            describe_content = describe_content.replace("\'", "")
    update_version=""
    update_info=""
    update_status="false"
    status_file="/td01/status.json"
    status={}
    try:
        fp=open(status_file,"rb")
        status=json.load(fp)
        fp.close()
    except Exception as e:
        update_status="false"
        status={"poc_version": "20190100", "code_version": "1.1.1", "rule_version": "20190100", "upgrade_url": "http://172.16.39.230:8100"}
    if update_version != None  and update_type != None:
        if update_type=="1":
           update_info="代码更新"
           status["code_version"]=update_version
           update_version="代码-"+update_version
        elif update_type=="2":
           update_info="漏洞库更新"
           status["poc_version"]=update_version
           status["rule_version"]=update_version
           update_version="漏洞库-"+update_version
    else:
        print "update_version != None  and update_type != None"
        return 
    fp=open(status_file,"wb")
    fp.write(json.dumps(status)) 
    fp.close()
    if updatestatus == "ok"  :
        update_status="true"
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect('/td01/update.db')
    c = conn.cursor()
    datas = (update_version, update_info, time, '', 'true', describe_content)
    conn.text_factory = str
    c.execute("insert into t_update(version_num,instruction,time,use_time,state,describe) values(?,?,?,?,?,?)", (datas));
    conn.commit()
    conn.close()
    os.system("rm -rf /td01/tupdate/*")
    
 
if __name__=="__main__":
    td01_install_after()