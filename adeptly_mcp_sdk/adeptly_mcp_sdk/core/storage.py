import os, datetime, json
def save_artifact(text: str, out_dir="out") -> str:
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(out_dir, f"artifact_{ts}.txt")
    with open(path,"w", encoding="utf-8") as f: f.write(text)
    return path

def log_run(data: dict, log_dir="logs"):
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir,"runs.jsonl"),"a", encoding="utf-8") as f:
        f.write(json.dumps(data)+"\n")
