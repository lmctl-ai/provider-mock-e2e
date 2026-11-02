"""Owned real CLI + loopback mock. No timers, output caps, credentials or live APIs."""
import argparse,json,os,pathlib,shutil,subprocess,sys,tempfile,urllib.request
EXPECTED='PROVIDER_MOCK_OK_129'
PROMPT='Reply with exactly '+EXPECTED+'. Do not call any tools.'

PACKAGES={'claude':'@anthropic-ai/claude-code','codex':'@openai/codex','gemini':'@google/gemini-cli','copilot':'@github/copilot','opencode':'opencode-ai','kimi':'@moonshot-ai/kimi-code','qwen':'@qwen-code/qwen-code','pi':'@earendil-works/pi-coding-agent','dsh':'@deepseek-ai/dsh','miniplayer':'miniplayer'}

def tool_argv(binary,args):
 binary=pathlib.Path(binary)
 if binary.suffix.lower()!='.cmd':return [str(binary)]+args
 # Bypass only npm's generated batch forwarding, not the installed tool. cmd.exe
 # consumes empty/quoted arguments differently; Node's argv layer preserves them.
 provider=binary.stem
 if provider not in PACKAGES:raise RuntimeError('unreviewed batch launcher: '+provider)
 package=binary.parent/'node_modules'/PACKAGES[provider]
 data=json.loads((package/'package.json').read_text(encoding='utf-8'))
 entry=data['bin'];entry=entry if isinstance(entry,str) else entry[provider]
 target=(package/entry).resolve()
 assert target.is_file() and target.is_relative_to(package.resolve()),'npm entry escaped owned package'
 if target.suffix.lower()=='.exe':return [str(target)]+args
 return [shutil.which('node'),str(target)]+args

def command(argv,env,cwd):
 argv=tool_argv(argv[0],argv[1:])
 return subprocess.run(argv,env=env,cwd=cwd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',errors='replace')

def clean_env(home):
 keep=['PATH','SystemRoot','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','TEMP','TMP','LANG','LC_ALL','TERM','PROCESSOR_ARCHITECTURE']
 env={k:os.environ[k] for k in keep if k in os.environ}
 env.update(HOME=str(home),USERPROFILE=str(home),XDG_CONFIG_HOME=str(home/'config'),XDG_DATA_HOME=str(home/'data'),XDG_CACHE_HOME=str(home/'cache'),XDG_STATE_HOME=str(home/'state'),LOCALAPPDATA=str(home/'local'),APPDATA=str(home/'roaming'),CI='true',NO_COLOR='1',DO_NOT_TRACK='1')
 return env

def configure(provider,base,home,work):
 env=clean_env(home);model='mock-agent';v1=base+'/v1';key='synthetic-mock-key-129';args=[]
 def write(name,data):
  p=home/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data);return str(p)
 if provider=='claude':
  env.update(CLAUDE_CONFIG_DIR=str(home/'claude'),ANTHROPIC_BASE_URL=base,ANTHROPIC_AUTH_TOKEN=key,ANTHROPIC_API_KEY='',ANTHROPIC_MODEL=model,DISABLE_PROMPT_CACHING='1',DISABLE_TELEMETRY='1',DISABLE_ERROR_REPORTING='1',DISABLE_AUTOUPDATER='1',CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',CLAUDE_CODE_DISABLE_TERMINAL_TITLE='1',CLAUDE_CODE_DISABLE_THINKING='1')
  args=['--bare','--setting-sources','','--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--no-session-persistence','--tools','','--model',model,'-p',PROMPT,'--output-format','json']
 elif provider=='codex':
  env.update(CODEX_HOME=str(home/'codex'),MOCK_API_KEY=key)
  write('codex/config.toml','model="mock-agent"\nmodel_provider="mock"\n[model_providers.mock]\nname="loopback"\nbase_url='+json.dumps(v1)+'\nwire_api="responses"\nenv_key="MOCK_API_KEY"\n[analytics]\nenabled=false\n')
  args=['exec','--skip-git-repo-check','--json',PROMPT]
 elif provider=='gemini':
  env.update(GEMINI_API_KEY=key,GOOGLE_GEMINI_BASE_URL=base,GEMINI_CLI_HOME=str(home),GEMINI_TELEMETRY_ENABLED='false',GEMINI_CLI_TRUST_WORKSPACE='true')
  write('.gemini/settings.json',json.dumps({'security':{'auth':{'selectedType':'gemini-api-key'}},'telemetry':{'enabled':False},'privacy':{'usageStatisticsEnabled':False},'general':{'disableAutoUpdate':True}}))
  args=['-m','gemini-2.5-flash','-p',PROMPT,'--output-format','json']
 elif provider=='qwen':
  env.update(OPENAI_API_KEY=key,OPENAI_BASE_URL=v1,OPENAI_MODEL=model,QWEN_TELEMETRY_ENABLED='false')
  write('.qwen/settings.json',json.dumps({'security':{'auth':{'selectedType':'openai'}},'telemetry':{'enabled':False}}))
  args=['-m',model,'-p',PROMPT,'--output-format','json']
 elif provider=='copilot':
  env.update(COPILOT_PROVIDER_BASE_URL=v1,COPILOT_PROVIDER_API_KEY=key,COPILOT_PROVIDER_TYPE='openai',COPILOT_MODEL=model,COPILOT_OFFLINE='true',COPILOT_TELEMETRY='off',COPILOT_SKIP_UPDATE_CHECK='1')
  args=['-p',PROMPT,'--model',model,'--silent','--no-ask-user']
 elif provider in ['opencode','lmplayer']:
  conf={'provider':{'mock':{'npm':'@ai-sdk/openai-compatible','name':'mock','options':{'baseURL':v1,'apiKey':key},'models':{model:{'name':model}}}},'model':'mock/'+model,'permission':{'*':'deny'}}
  confpath=write('provider.json',json.dumps(conf))
  env.update(OPENCODE_CONFIG=confpath,OPENCODE_DISABLE_MODELS_FETCH='true',OPENCODE_DISABLE_AUTOUPDATE='true',OPENCODE_DISABLE_DEFAULT_PLUGINS='true',LMPLAYER_CONFIG=confpath)
  args=['run','--model','mock/'+model,'--format','json',PROMPT]
 elif provider=='pi':
  env['PI_CODING_AGENT_DIR']=str(home/'pi')
  write('pi/models.json',json.dumps({'providers':{'mock':{'baseUrl':v1,'api':'openai-completions','apiKey':key,'models':[{'id':model}]}}}))
  args=['--provider','mock','--model',model,'--no-session','--no-tools','-p',PROMPT]
 elif provider=='kimi':
  config='default_model="mock"\n[providers.mock]\ntype="openai"\nbase_url='+json.dumps(v1)+'\napi_key='+json.dumps(key)+'\n[models.mock]\nprovider="mock"\nmodel="mock-agent"\nmax_context_size=128000\n'
  write('.kimi-code/config.toml',config)
  args=['-p',PROMPT,'--output-format','stream-json']
 elif provider=='miniplayer':
  confpath=write('miniplayer.json',json.dumps({'provider':{'openai':{'baseURL':v1,'apiKey':key}}}))
  env['OPENAI_API_KEY']=key
  env['MINIPLAYER_CONFIG']=confpath
  args=['run','--model','openai/mock-agent',PROMPT]
 elif provider=='agy':
  env.update(GEMINI_API_KEY=key,GOOGLE_GEMINI_BASE_URL=base,AGY_TELEMETRY_DISABLED='1',DO_NOT_TRACK='1')
  write('.gemini/antigravity-cli/settings.json',json.dumps({'modelProvider':'gemini','telemetry':{'enabled':False}}))
  args=['-p',PROMPT,'--model','gemini-3.8-flash']
 elif provider=='hermes':
  env.update(HERMES_HOME=str(home/'hermes'),OPENAI_BASE_URL=v1,OPENAI_API_KEY=key,HERMES_TELEMETRY_ENABLED='false')
  args=['chat','--native','--provider','custom','--base-url',v1,'--api-key',key,'--model',model,'--safe-mode','-Q','-q',PROMPT]
 elif provider=='muse':
  env.update(META_API_KEY=key,MUSE_NO_AUTO_UPDATE='1')
  args=['exec','--provider','meta','--base-url',v1,'--model','muse-spark-1.2',PROMPT]
 elif provider=='dsh':
  env.update(DSH_HOME=str(home/'dsh'),DEEPSEEK_API_KEY=key,DEEPSEEK_BASE_URL=v1,DSH_TELEMETRY_DISABLED='1')
  args=['headless',PROMPT]
 else:raise ValueError('provider not configured: '+provider)
 return env,args

def reply(provider,stdout):
 if provider=='claude':return json.loads(stdout)['result']
 if provider=='kimi':
  rows=[json.loads(x) for x in stdout.splitlines() if x.startswith('{')]
  answers=[x['content'] for x in rows if x.get('role')=='assistant'];assert len(answers)==1,rows
  return answers[0]
 if provider=='gemini':return json.loads(stdout)['response']
 if provider=='qwen':
  rows=json.loads(stdout);results=[x for x in rows if x.get('type')=='result'];assert len(results)==1 and not results[0].get('is_error');return results[0]['result']
 if provider=='codex':
  rows=[json.loads(x) for x in stdout.splitlines() if x.startswith('{')]
  return ''.join(x['item']['text'] for x in rows if x.get('type')=='item.completed' and x.get('item',{}).get('type')=='agent_message')
 if provider in ['opencode','lmplayer']:
  rows=[json.loads(x) for x in stdout.splitlines() if x.startswith('{')]
  return ''.join(x['part']['text'] for x in rows if x.get('type')=='text')
 return stdout.strip()

def oracle(observed,expected):
 if observed!=expected:raise AssertionError('wrong-reply: expected '+repr(expected)+' received '+repr(observed))

def child(provider,binary,out):
 base=os.environ['LMMOCK_URL'];url=urllib.parse.urlparse(base)
 assert url.hostname in ['127.0.0.1','::1'] and url.scheme=='http','non-loopback endpoint refused'
 with tempfile.TemporaryDirectory(prefix='provider-home-') as scratch:
  home=pathlib.Path(scratch);work=home/'work';work.mkdir()
  env,args=configure(provider,base,home,work)
  version=command([binary,'--version'],env,work)
  try:r=command([binary]+args,env,work)
  finally:
   if provider=='hermes':
    interpreter=pathlib.Path(binary).parent/('python.exe' if os.name=='nt' else 'python')
    subprocess.run([str(interpreter),str(pathlib.Path(__file__).with_name('cleanup-hermes.py')),str(home/'hermes')],env=env,cwd=work,check=True)
  out.mkdir(parents=True,exist_ok=True)
  (out/'stdout.txt').write_text(r.stdout,encoding='utf-8');(out/'stderr.txt').write_text(r.stderr,encoding='utf-8')
  (out/'version.txt').write_text(version.stdout+version.stderr,encoding='utf-8')
  inspect=json.load(urllib.request.urlopen(base+'/__inspect'))
  (out/'request.json').write_text(json.dumps(inspect,indent=2))
  if r.returncode==0:
   assert inspect.get('method')=='POST','no prompt POST recorded'
   assert PROMPT in inspect.get('body',''),'exact prompt absent from mock request'
   expected_path={'claude':'/v1/messages','codex':'/v1/responses','gemini':'/v1beta/models/','qwen':'/v1/chat/completions','copilot':'/v1/chat/completions','opencode':'/v1/chat/completions','pi':'/v1/chat/completions','kimi':'/v1/chat/completions','miniplayer':'/v1/responses','lmplayer':'/v1/chat/completions','agy':'/v1beta/models/','dsh':'/v1/messages','hermes':'/v1/chat/completions'}[provider]
   assert inspect.get('url','').startswith(expected_path),'wrong provider endpoint'
  assert r.returncode==0,'tool exit '+str(r.returncode)+': '+r.stderr
  actual=reply(provider,r.stdout);oracle(actual,EXPECTED)
  try:oracle(actual,'DELIBERATELY_WRONG_129')
  except AssertionError as e:
   assert str(e).startswith('wrong-reply:');control='CAUGHT wrong-reply assertion'
  else:raise AssertionError('wrong expectation control survived')
  result={'provider':provider,'exit':r.returncode,'reply':actual,'version':version.stdout.strip(),'control':control,'os':sys.platform}
  (out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

def main():
 p=argparse.ArgumentParser();p.add_argument('provider');p.add_argument('--binary',required=True);p.add_argument('--settings',required=True);p.add_argument('--out',required=True);p.add_argument('--child',action='store_true');a=p.parse_args();out=pathlib.Path(a.out).resolve()
 if a.child:return child(a.provider,a.binary,out)
 out.mkdir(parents=True,exist_ok=True);settings=json.loads(pathlib.Path(a.settings).read_text());config=out/'config.json';config.write_text(json.dumps({'text':EXPECTED}))
 argv=[settings['binary'],'exec','--lmcode',settings['program'],'--config',str(config),'--audit-log',str(out/'audit.jsonl'),'--',sys.executable,str(pathlib.Path(__file__).resolve()),a.provider,'--binary',a.binary,'--settings',a.settings,'--out',str(out),'--child']
 subprocess.run(argv,check=True)
 audit=[json.loads(x) for x in (out/'audit.jsonl').read_text().splitlines()]
 posts=[x for x in audit if x.get('method')=='POST' and x.get('status')==200]
 assert posts,'no successful real POST observed by lmmock'
 print(json.dumps({'provider':a.provider,'audit_posts':[{k:x[k] for k in ['method','url','status']} for x in posts]}))
if __name__=='__main__':main()
