"""Portable prediction and independently pinned release verification (no pickle)."""
import json,hashlib,math
from pathlib import Path

class ModelError(ValueError): pass

def read(path):
    p=Path(path)
    if p.stat().st_size>262144: raise ModelError("Oversized model or policy")
    obj=json.loads(p.read_text(),parse_constant=lambda x:(_ for _ in ()).throw(ModelError("Nonfinite JSON")))
    if not isinstance(obj,dict):raise ModelError("Expected object")
    return obj

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def validate(model):
    if model.get("schema")!="skylinee-linear/v1":raise ModelError("Unknown schema")
    names=model.get("features")
    if not isinstance(names,list) or not names or len(names)>32 or len(names)!=len(set(names)):raise ModelError("Invalid features")
    if len(model.get("coefficients",[]))!=len(names):raise ModelError("Coefficient mismatch")
    if set(model.get("training_ranges",{}))!=set(names):raise ModelError("Missing ranges")
    if not all(math.isfinite(float(v)) for v in [model["intercept"]]+model["coefficients"]):raise ModelError("Nonfinite model")
    return model

def predict(model,values):
    validate(model)
    if not isinstance(values,dict) or set(values)!=set(model["features"]):raise ModelError("Expected exactly: "+str(model["features"]))
    if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in values.values()):raise ModelError("Invalid numeric input")
    y=math.fsum([model["intercept"]]+[c*values[k] for k,c in zip(model["features"],model["coefficients"])])
    if not math.isfinite(y):raise ModelError("Nonfinite result")
    outside=[k for k,v in values.items() if not model["training_ranges"][k][0]<=v<=model["training_ranges"][k][1]]
    return {"prediction":y,"outside_training_range":outside,"caution":"Extrapolation; accuracy may degrade" if outside else None}

def release_policy(path):
    m=validate(read(path))
    low={k:m["training_ranges"][k][0] for k in m["features"]}
    high={k:m["training_ranges"][k][1] for k in m["features"]}
    mid={k:(low[k]+high[k])/2 for k in low}
    extrap={k:high[k]+.2*max(high[k]-low[k],1) for k in low}
    return {"schema":"skylinee-linear-release/v1","sha256":digest(path),"rtol":1e-9,"atol":1e-9,
            "reference":[{"features":v,"expected":predict(m,v)["prediction"]} for v in [low,mid,high,extrap]]}

def verify(path,policy_path):
    m=validate(read(path));p=read(policy_path)
    if p.get("schema")!="skylinee-linear-release/v1":raise ModelError("Policy schema mismatch")
    if digest(path)!=p["sha256"]:raise ModelError("REJECTED: artifact digest mismatch")
    rtol,atol=p["rtol"],p["atol"]
    if not 0<=rtol<=1 or not 0<=atol<=1:raise ModelError("Invalid tolerances")
    if len(p["reference"])<4:raise ModelError("Insufficient reference vectors")
    for i,r in enumerate(p["reference"]):
        y=predict(m,r["features"])["prediction"]
        if not math.isclose(y,r["expected"],rel_tol=rtol,abs_tol=atol):raise ModelError(f"REJECTED: vector {i} differs")
    return {"status":"PASS","sha256":digest(path),"references":len(p["reference"])}
