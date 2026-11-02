"""Exercise released stock fixture shapes; never calls tools or external APIs."""
import json,os,pathlib,subprocess,sys,urllib.request
cases=[
 ('chat','/v1/chat/completions',{'model':'mock-agent','messages':[{'role':'user','content':'wire-shape'}]}, {'tools':[{'type':'function','function':{'name':'weather','parameters':{'type':'object'}}}]},'tool_calls','[DONE]'),
 ('responses','/v1/responses',{'model':'mock-agent','input':'wire-shape'}, {'tools':[{'type':'function','name':'weather','parameters':{'type':'object'}}]},'function_call','response.completed'),
 ('anthropic','/v1/messages',{'model':'mock-agent','messages':[{'role':'user','content':'wire-shape'}]}, {'tools':[{'name':'weather','input_schema':{'type':'object'}}]},'tool_use','message_stop'),
 ('gemini','/v1beta/models/mock-agent:streamGenerateContent?alt=sse',{'contents':[{'role':'user','parts':[{'text':'wire-shape'}]}]}, {'tools':[{'functionDeclarations':[{'name':'weather','parameters':{'type':'object'}}]}]},'functionCall','STOP'),
 ('ollama','/api/chat',{'model':'mock-agent','messages':[{'role':'user','content':'wire-shape'}]}, {'tools':[{'type':'function','function':{'name':'weather','parameters':{'type':'object'}}}]},'tool_calls','"done":true')]
if len(sys.argv)>1 and sys.argv[1]=='--child':
 out=pathlib.Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
 for name,url,body,tools,toolmarker,terminal in cases:
  for mode in ['text','tool']:
   payload={**body,'stream':True,**(tools if mode=='tool' else {})}
   req=urllib.request.Request(os.environ['LMMOCK_URL']+url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer synthetic-mock-key-129','x-api-key':'synthetic-mock-key-129','anthropic-version':'2023-06-01'})
   with urllib.request.urlopen(req) as r:data=r.read().decode();status=r.status;ctype=r.headers['Content-Type']
   (out/(name+'-'+mode+'.txt')).write_text(data)
   assert status==200 and ('event-stream' in ctype or 'ndjson' in ctype),name+' stream framing'
   assert terminal in data,name+' terminal'
   assert ('weather' in data and toolmarker in data) if mode=='tool' else 'PROVIDER_MOCK_OK_129' in data,name+' payload'
   try:assert 'DELIBERATELY_WRONG_129' in data,'wrong-reply wire control'
   except AssertionError:pass
   else:raise AssertionError('wire control survived')
   print('PASS stock '+name+'/'+mode+' and wrong-reply control')
else:
 settings=json.loads(pathlib.Path(sys.argv[1]).read_text());out=pathlib.Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
 config=out/'wire-config.json';config.write_text(json.dumps({'text':'PROVIDER_MOCK_OK_129'}))
 subprocess.run([settings['binary'],'exec','--lmcode',settings['stock_program'],'--config',str(config),'--audit-log',str(out/'wire-audit.jsonl'),'--',sys.executable,str(pathlib.Path(__file__).resolve()),'--child',str(out)],check=True)
