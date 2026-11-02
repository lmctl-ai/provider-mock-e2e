import importlib.util,pathlib,unittest
spec=importlib.util.spec_from_file_location('probe',pathlib.Path(__file__).parents[1]/'scripts/probe.py');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
class OracleTests(unittest.TestCase):
 def test_exact(self):probe.oracle(probe.EXPECTED,probe.EXPECTED)
 def test_wrong_expectation(self):
  with self.assertRaisesRegex(AssertionError,'wrong-reply:'):probe.oracle(probe.EXPECTED,'wrong')
 def test_extra_text_is_not_exact(self):
  with self.assertRaisesRegex(AssertionError,'wrong-reply:'):probe.oracle(probe.EXPECTED+' trailing',probe.EXPECTED)
 def test_npm_entry_preserves_arguments(self):
  import tempfile,json
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);package=root/'node_modules/@openai/codex';package.mkdir(parents=True)
   (package/'package.json').write_text(json.dumps({'bin':{'codex':'entry.js'}}));(package/'entry.js').touch()
   args=['',probe.PROMPT,'{"x":"a b"}']
   self.assertEqual(probe.tool_argv(root/'codex.cmd',args)[2:],args)
 def test_credentials_not_inherited(self):
  import os,tempfile
  from unittest.mock import patch
  with patch.dict(os.environ,{'OPENAI_API_KEY':'must-not-leak','GH_TOKEN':'must-not-leak'}):
   env=probe.clean_env(pathlib.Path(tempfile.gettempdir()))
   self.assertNotIn('OPENAI_API_KEY',env);self.assertNotIn('GH_TOKEN',env)
if __name__=='__main__':unittest.main()
