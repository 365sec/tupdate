import argparse
import json
import os
from  tupdate import pkt_key
from  tupdate.utils import rc4Decrypt,un_zip


def return_output(data):   
    print json.dumps(data,ensure_ascii=False)
    
    
def td01_install_pkt():
    parser=argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file')
    args = parser.parse_args()
    
    if args.input_file == None  :
       return_output({"td01_install_pkt":"usage td01_install_pkt -i file"})
       return 
    try:
        os.system("rm -rf /td01/tupdate/*")
        rc4Decrypt(args.input_file,args.input_file,pkt_key) 
        un_zip(args.input_file,"/td01/tupdate") 
        os.system("cd /td01/tupdate/ && chmod +x update.sh && ./update.sh 2>&1 >/dev/null")
        return_output({"td01_install_pkt":"ok"})
    except Exception as e:
        return_output({"td01_install_pkt":str(e)})
    
if __name__ == "__main__":
    td01_install_pkt()