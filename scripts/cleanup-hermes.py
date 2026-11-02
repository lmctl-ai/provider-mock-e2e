"""Reap only a gateway recorded under this invocation's fresh Hermes HOME."""
import json,os,pathlib,sys

def validate_record(record,home):
 assert record['kind']=='hermes-gateway','unexpected process kind'
 assert pathlib.Path(record['hermes_home']).resolve()==home.resolve(),'foreign Hermes HOME refused'
 assert isinstance(record['pid'],int) and record['pid']>0,'invalid owned PID'
 assert record.get('start_time') is not None,'missing process identity'
 return record['pid']

def main():
 home=pathlib.Path(sys.argv[1]).resolve();recordfile=home/'gateway.pid'
 if not recordfile.exists():return
 record=json.loads(recordfile.read_text(encoding='utf-8'));pid=validate_record(record,home)
 # The bundled dependency and fingerprint helper use process identity, not an
 # argv scan. A fresh HOME had no gateway before this tool invocation.
 import psutil
 from gateway.status import get_process_start_time,_start_times_agree
 try:
  process=psutil.Process(pid)
  assert _start_times_agree(get_process_start_time(pid),record['start_time']),'reused PID refused'
  assert pathlib.Path(process.environ()['HERMES_HOME']).resolve()==home,'live process HOME disagrees'
  assert 'gateway' in process.cmdline() and 'run' in process.cmdline(),'not the recorded gateway'
  if hasattr(os,'pidfd_open'):
   import select
   fd=os.pidfd_open(pid)
   try:process.kill();select.select([fd],[],[])
   finally:os.close(fd)
  else:
   process.kill();process.wait()
  print(json.dumps({'owned_gateway_pid':pid,'reaped':True}))
 except psutil.NoSuchProcess:print(json.dumps({'owned_gateway_pid':pid,'already_exited':True}))
if __name__=='__main__':main()
