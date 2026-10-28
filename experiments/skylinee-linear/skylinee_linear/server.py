"""Local-only JSON inference API. Use an authenticated reverse proxy for remote access."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .model import ModelError, predict, read, validate, verify

def serve(model_path,policy_path,host="127.0.0.1",port=5055):
    approved=verify(model_path,policy_path)
    model=validate(read(model_path))
    class Handler(BaseHTTPRequestHandler):
        def respond(self,code,data):
            raw=json.dumps(data,allow_nan=False).encode()
            self.send_response(code);self.send_header("Content-Type","application/json")
            self.send_header("Content-Length",str(len(raw)));self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff");self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            if self.path=="/health":return self.respond(200,{"status":"ready","verified":True,"sha256":approved["sha256"]})
            if self.path=="/schema":return self.respond(200,{"features":model["features"],"target":model["target"]})
            self.respond(404,{"error":"unknown endpoint"})
        def do_POST(self):
            if self.path not in ("/predict","/batch"):return self.respond(404,{"error":"unknown endpoint"})
            if self.headers.get("Content-Type","").split(";")[0].strip().lower()!="application/json":return self.respond(415,{"error":"JSON required"})
            length=self.headers.get("Content-Length","")
            if not length.isdigit() or not 0<int(length)<=65536:return self.respond(413,{"error":"body exceeds 64KB"})
            try:
                obj=json.loads(self.rfile.read(int(length)),parse_constant=lambda _:(_ for _ in ()).throw(ModelError("Nonfinite JSON")))
                if not isinstance(obj,dict):raise ModelError("JSON object required")
                if self.path=="/predict":
                    if set(obj)!={"features"}:raise ModelError("Expected features")
                    res=predict(model,obj["features"])
                else:
                    if set(obj)!={"rows"} or not isinstance(obj["rows"],list) or len(obj["rows"])>1000:raise ModelError("Expected <=1000 rows")
                    res={"results":[predict(model,row) for row in obj["rows"]]}
                self.respond(200,res)
            except (ValueError,TypeError) as e:self.respond(400,{"error":str(e)})
    if host not in ("localhost","127.0.0.1","::1"):print("WARNING: No authentication or TLS; protect the endpoint.")
    print(f"Verified artifact {approved['sha256']}; listening on {host}:{port}")
    ThreadingHTTPServer((host,port),Handler).serve_forever()
