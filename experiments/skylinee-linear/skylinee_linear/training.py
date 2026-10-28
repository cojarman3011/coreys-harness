"""Numerical CSV regression, deterministic holdout, and release serialization."""
import csv,json,math,random
from pathlib import Path
from .model import ModelError,release_policy

def train_csv(path,target,features,no_intercept=False,ridge=0.,test_fraction=.2,seed=42):
    import numpy as np
    if not .1<=test_fraction<=.4 or not math.isfinite(ridge) or ridge<0:raise ModelError("Invalid split or ridge strength")
    if len(set(features))!=len(features) or len(features)>32 or target in features:raise ModelError("Invalid feature list")
    xs=[];ys=[]
    with open(path,newline="",encoding="utf-8-sig") as f:
        rd=csv.DictReader(f)
        if not rd.fieldnames or not set(features+[target]).issubset(rd.fieldnames):raise ModelError("Required CSV headers not found")
        for i,row in enumerate(rd):
            if i>=250000:raise ModelError("Dataset too large")
            try: v=[float(row[k]) for k in features];y=float(row[target])
            except (ValueError,TypeError):raise ModelError(f"Non-numeric row {i+2}")
            if not all(math.isfinite(n) for n in v+[y]):raise ModelError("Nonfinite CSV value")
            xs.append(v);ys.append(y)
    if len(ys)<max(12,3*(len(features)+1)):raise ModelError("Insufficient training data")
    indices=list(range(len(ys)));random.Random(seed).shuffle(indices)
    ntest=max(2,round(len(ys)*test_fraction));train=indices[ntest:];test=indices[:ntest]
    x=np.asarray([xs[i] for i in train]);y=np.asarray([ys[i] for i in train])
    xt=np.asarray([xs[i] for i in test]);yt=np.asarray([ys[i] for i in test])
    mx=np.zeros(len(features)) if no_intercept else x.mean(axis=0)
    my=0. if no_intercept else y.mean()
    xc=x-mx;yc=y-my
    a=np.vstack((xc,np.sqrt(ridge)*np.eye(x.shape[1]))) if ridge else xc
    b=np.r_[yc,np.zeros(len(features))] if ridge else yc
    beta,_,rank,_=np.linalg.lstsq(a,b,rcond=None)
    if rank<len(features):raise ModelError("Linearly dependent predictors")
    intercept=float(my-np.dot(mx,beta));err=yt-(xt@beta+intercept)
    denom=np.sum((yt-yt.mean())**2)
    return {"schema":"skylinee-linear/v1","target":target,"features":features,
            "coefficients":beta.tolist(),"intercept":intercept,
            "training_ranges":{k:[float(x[:,i].min()),float(x[:,i].max())] for i,k in enumerate(features)},
            "training_rows":len(train),"holdout_rows":len(test),
            "metrics":{"rmse":float(np.sqrt(np.mean(err**2))),"mae":float(np.mean(np.abs(err))),"r2":float(1-np.sum(err**2)/denom) if denom>0 else None},
            "method":"ridge" if ridge else "ordinary_least_squares"}

def save_release(model,model_path,policy_path):
    if Path(model_path).resolve()==Path(policy_path).resolve() or Path(model_path).exists() or Path(policy_path).exists():raise ModelError("Paths must differ; overwriting prohibited")
    Path(model_path).write_text(json.dumps(model,sort_keys=True,allow_nan=False))
    Path(policy_path).write_text(json.dumps(release_policy(model_path),sort_keys=True,allow_nan=False))
