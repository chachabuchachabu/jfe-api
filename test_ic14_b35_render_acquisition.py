import importlib.util,pathlib,tempfile,json,unittest
from unittest.mock import patch
P=pathlib.Path(__file__).parent/"tools/acquisition_smoke.py";s=importlib.util.spec_from_file_location("b35",P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class R:
 status=200;headers={"Content-Type":"text/html"}
 def __enter__(self):return self
 def __exit__(self,*a):pass
 def read(self):return b"official-test-body"
def load(p):
 with open(p) as f:return json.load(f)
class T(unittest.TestCase):
 def p(self):return tempfile.NamedTemporaryFile(delete=False).name
 def test_success(self):
  p=self.p()
  with patch.object(m.urllib.request,"urlopen",return_value=R()):self.assertEqual(m.run("https://example.test",p),0)
  self.assertEqual(load(p)["state"],"AVAILABLE")
 def test_hash(self):
  p=self.p()
  with patch.object(m.urllib.request,"urlopen",return_value=R()):m.run("https://example.test",p)
  self.assertEqual(len(load(p)["content_sha256"]),64)
 def test_http_error(self):
  p=self.p();e=m.urllib.error.HTTPError("https://x",403,"Forbidden",{},None)
  with patch.object(m.urllib.request,"urlopen",side_effect=e):m.run("https://x",p)
  x=load(p);self.assertEqual(x["error_type"],"HTTP_ERROR");self.assertNotEqual(x["state"],"NOT_PUBLISHED")
 def test_network_error(self):
  p=self.p()
  with patch.object(m.urllib.request,"urlopen",side_effect=m.urllib.error.URLError("dns")):m.run("https://x",p)
  self.assertEqual(load(p)["error_type"],"NETWORK_ERROR")
 def test_timezone(self):
  p=self.p()
  with patch.object(m.urllib.request,"urlopen",return_value=R()):m.run("https://x",p)
  self.assertIn("+",load(p)["acquired_at"])
 def test_provenance(self):
  p=self.p()
  with patch.object(m.urllib.request,"urlopen",return_value=R()):m.run("https://x",p)
  x=load(p);self.assertEqual((x["parser_version"],x["transport"]),("ic1.4-dev-b35","RENDER_HTTP"))
if __name__=="__main__":unittest.main()
