#coding:utf-8
import argparse 
from tupdate.utils import make_zip ,rc4Encrypt,rc4Decrypt
  
  
def td01_make_pkt():
    parser=argparse.ArgumentParser()
    parser.add_argument('-i', '--input-dir')
    parser.add_argument('-o', '--output-file')
    args = parser.parse_args()
    
    if args.input_dir == None or args.output_file == None:
        return 
    make_zip(args.input_dir,args.output_file)
    rc4Encrypt(args.output_file,args.output_file,"key")
 

    

if __name__== "__main__":
    td01_make_pkt()