import argparse

import yaml
from dotenv import load_dotenv

from . import db, pipeline


def main():
    load_dotenv()
    ap = argparse.ArgumentParser(prog="leadbot")
    ap.add_argument("cmd", choices=["find", "qualify", "send", "run", "serve", "stats"])
    ap.add_argument("--config", default="config.yaml")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config, encoding="utf-8"))
    con = db.connect()
    if a.cmd == "serve":
        import uvicorn
        from . import webhook
        webhook.CFG.update(cfg)
        uvicorn.run(webhook.app, host="0.0.0.0", port=8000)
    elif a.cmd == "stats":
        for r in con.execute("SELECT status, COUNT(*) n FROM leads GROUP BY status"):
            print(f"{r['status']:15}{r['n']}")
    else:
        getattr(pipeline, "run_all" if a.cmd == "run" else a.cmd)(cfg, con)


if __name__ == "__main__":
    main()
