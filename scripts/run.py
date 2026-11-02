import argparse,json,os,pathlib,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('provider');p.add_argument('--settings',required=True);p.add_argument('--out',required=True);a=p.parse_args()
r=subprocess.run(['lminstall','status',a.provider,'--json'],check=True,stdout=subprocess.PIPE,text=True)
row=json.loads(r.stdout)[0]
assert row['state']=='installed',row
subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('probe.py')),a.provider,'--binary',row['binary'],'--settings',a.settings,'--out',a.out],check=True)
