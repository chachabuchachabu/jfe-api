import json, os, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

VERSION="0.8.1"
STARTED=time.time()

def health():
    return 200, {
        "service":"JFE","version":VERSION,"status":"UP",
        "mode":os.getenv("JFE_MODE","qualification"),
        "uptime_s":round(time.time()-STARTED,2)
    }

def race(date,venue,race_no):
    return 503, {
        "service":"JFE","version":VERSION,
        "status":"SOURCE_ADAPTERS_PENDING",
        "request":{"date":date,"venue":venue,"race_no":int(race_no)},
        "message":"Deployment qualified; live source adapters connect in v0.9."
    }

class Handler(BaseHTTPRequestHandler):
    def send_json(self,code,body):
        raw=json.dumps(body,ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(raw)))
        self.send_header("Cache-Control","no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path=self.path.split("?",1)[0]
        if path in ("/","/health"):
            return self.send_json(*health())
        parts=[unquote(x) for x in path.strip("/").split("/")]
        if len(parts)==5 and parts[:2]==["v1","race"]:
            try:
                return self.send_json(*race(parts[2],parts[3],parts[4]))
            except Exception as e:
                return self.send_json(400,{"status":"BAD_REQUEST","detail":str(e)})
        return self.send_json(404,{"status":"NOT_FOUND"})

    def log_message(self,fmt,*args):
        print(json.dumps({"event":"http","message":fmt%args}),flush=True)

def main():
    port=int(os.getenv("PORT","10000"))
    print(json.dumps({"event":"startup","service":"JFE","version":VERSION,"port":port}),flush=True)
    ThreadingHTTPServer(("0.0.0.0",port),Handler).serve_forever()

if __name__=="__main__":
    main()
