import os ,json , datetime
os.makedirs("logs", exist_ok=True)
def log_tool_call(name , args, result ,status):
    """写工具日志"""
    path ="logs/" + datetime.datetime.now().strftime("%Y-%m-%d") + "_tools.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp" : datetime.datetime.now().strftime("%Y%m%d_%H%M%S") ,
            "tool" : name ,
            "input" : args,
            "output_summary" : result[:200] + ("..." if len(result) > 200 else "") ,
            "status": status
        }, ensure_ascii=False) + "\n") 
def read_tool_log(name):
    """读工具日志"""
    path = f"logs/{name}.jsonl"
    with open(path, "r", encoding="utf-8") as f:
        logs = [json.loads(line) for line in f if line.strip()]
    return logs
