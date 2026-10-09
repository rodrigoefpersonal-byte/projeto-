import argparse

import yaml
from dotenv import load_dotenv

from . import db, pipeline


def main():
    load_dotenv()
    ap = argparse.ArgumentParser(prog="leadbot")
    ap.add_argument("cmd", choices=["find", "qualify", "send", "run", "serve", "stats", "dm", "dm-done", "import"])
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--niche", help="testar só este nicho (ex.: dentista)")
    ap.add_argument("--city", help="testar só esta cidade (ex.: \"Curitiba, PR\")")
    ap.add_argument("args", nargs="*", help="ids (dm-done) ou arquivo.csv (import)")
    a = ap.parse_args()
    import os
    if not os.path.exists(a.config) and a.config == "config.yaml":
        a.config = "config.example.yaml"  # sem config.yaml, usa o modelo (já vem no modo grátis)
    cfg = yaml.safe_load(open(a.config, encoding="utf-8"))
    if a.niche:
        cfg["search"]["niches"] = {k: [a.niche] for k in cfg["search"]["niches"]}
    if a.city:
        for tg in cfg["search"]["targets"]:
            tg["cities"] = [a.city]
    con = db.connect()
    if a.cmd == "serve":
        import uvicorn
        from . import webhook
        webhook.CFG.update(cfg)
        uvicorn.run(webhook.app, host="0.0.0.0", port=8000)
    elif a.cmd == "stats":
        for r in con.execute("SELECT status, COUNT(*) n FROM leads GROUP BY status"):
            print(f"{r['status']:15}{r['n']}")
    elif a.cmd == "dm":
        pipeline.dm_queue(cfg, con)
    elif a.cmd == "dm-done":
        pipeline.dm_done(con, [int(i) for i in a.args])
    elif a.cmd == "import":
        pipeline.import_csv(cfg, con, a.args[0])
    else:
        getattr(pipeline, "run_all" if a.cmd == "run" else a.cmd)(cfg, con)


if __name__ == "__main__":
    main()
