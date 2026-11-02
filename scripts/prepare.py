"""Download a release (binary and examples), verify both, compile owned policy."""
import hashlib,json,os,pathlib,platform,subprocess,sys,tarfile,urllib.request
root=pathlib.Path(os.environ.get('MOCK_ROOT',str(pathlib.Path(os.environ.get('RUNNER_TEMP','/tmp'))/'provider-mock-tools'))).resolve()
root.mkdir(parents=True,exist_ok=True)
tag='v0.1.94'
arch={'x86_64':'x64','AMD64':'x64','aarch64':'arm64','arm64':'arm64'}[platform.machine()]
kind={'Linux':'linux','Darwin':'macos','Windows':'windows'}[platform.system()]
asset='lmmock-'+kind+'-'+arch+('.exe' if kind=='windows' else '')
for name in ['SHA256SUMS',asset,'examples.tar.gz']:
 dest=root/name
 if not dest.exists():urllib.request.urlretrieve('https://github.com/lmctl-ai/lmmock/releases/download/'+tag+'/'+name,dest)
sums={row.split()[1].lstrip('*'):row.split()[0] for row in (root/'SHA256SUMS').read_text().splitlines()}
for name in [asset,'examples.tar.gz']:
 actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
 if actual!=sums.get(name):raise RuntimeError('release checksum mismatch: '+name)
(root/asset).chmod(0o700)
with tarfile.open(root/'examples.tar.gz') as tar:tar.extractall(root,filter='data')
# Stock fixtures force the first advertised tool using Paris-shaped arguments.
# A no-tool prompt must get a text answer even if the CLI advertises built-ins.
# This is fixture policy, not a provider client shim or a wire rewrite.
source=(root/'examples/llm-api.lms').read_text()
for old in ['if (request.has("tools") && !tool_result)', 'if (b.has("tools") && !tool_result)']:
 if old not in source:raise RuntimeError('released policy anchor missing')
 source=source.replace(old,'if (false)')
(root/'examples/no-tools.lms').write_text(source)
compiler=os.environ.get('LMSCRIPT_JS')
if not compiler:raise RuntimeError('LMSCRIPT_JS must name private compiler bin/lmscript')
for name in ['llm-api','no-tools']:
 subprocess.run(['node',compiler,'--no-preflight',str(root/'examples'/ (name+'.lms')),str(root/(name+'.dslb'))],check=True)
settings={'root':str(root),'binary':str(root/asset),'program':str(root/'no-tools.dslb'),'stock_program':str(root/'llm-api.dslb'),'release':tag,'sha256':sums[asset]}
(root/'settings.json').write_text(json.dumps(settings,indent=2))
print(json.dumps(settings))
