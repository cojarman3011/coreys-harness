"""Skylinee Linear CLI: train, verify, predict, serve."""
import argparse
import json
import sys

from .model import predict, read, validate, verify
from .training import save_release, train_csv


def main(argv=None):
    p=argparse.ArgumentParser(description="Skylinee Linear portable regression")
    sub=p.add_subparsers(dest="command",required=True)
    t=sub.add_parser("train");t.add_argument("--csv",required=True);t.add_argument("--target",required=True);t.add_argument("--features",nargs="+",required=True)
    t.add_argument("--model",default="model.json");t.add_argument("--policy",default="release_policy.json")
    t.add_argument("--no-intercept",action="store_true");t.add_argument("--ridge",type=float,default=0.);t.add_argument("--test-fraction",type=float,default=.2);t.add_argument("--seed",type=int,default=42)
    for command in ("verify","predict","serve"):
        q=sub.add_parser(command);q.add_argument("--model",required=True);q.add_argument("--policy",required=True)
        if command=="predict":q.add_argument("--features-json",required=True)
        if command=="serve":q.add_argument("--port",type=int,default=5055);q.add_argument("--host",default="127.0.0.1")
    a=p.parse_args(argv)
    try:
        if a.command=="train":
            m=train_csv(a.csv,a.target,a.features,a.no_intercept,a.ridge,a.test_fraction,a.seed)
            save_release(m,a.model,a.policy);result={"trained":True,"metrics":m["metrics"],"coefficients":m["coefficients"],"intercept":m["intercept"]}
        elif a.command=="verify":result=verify(a.model,a.policy)
        elif a.command=="predict":
            verify(a.model,a.policy);result=predict(validate(read(a.model)),json.loads(a.features_json))
        else:
            from .server import serve
            serve(a.model,a.policy,a.host,a.port);return 0
        print(json.dumps(result,indent=2));return 0
    except (OSError,ValueError,TypeError) as e:
        print("ERROR:",e,file=sys.stderr);return 2

if __name__=="__main__":sys.exit(main())
