"""my-agent smoke test - 回归基线（W4 重构 agent.py 前锁定）
覆盖: config(context_window) / credentials / permission(classify + _check_permission + dispatch_tool) / _trim_to_budget
运行: venv/bin/python smoke_test.py   (非交互，input 已 mock)
TODO 后补: log_tool_call 落盘 / plan 模式开关
"""
import tools, config
from agent import Agent

def make_input(ans):
    return lambda prompt="": ans

allok = True
def check(cond, msg):
    global allok
    allok = allok and cond
    print(f"  [{'OK' if cond else 'FAIL'}] {msg}")

print("=== 1. config: context_window 透传 ===")
c = config.get_config()
check("context_window" in c, f"get_config 有 context_window = {c.get('context_window')}")
check(isinstance(c.get("context_window"), int) and c["context_window"] > 0, "context_window 是正整数")
check(config.resolve_credential("不存在的凭证") is None, "不存在凭证返回 None")

print("\n=== 2. credentials: resolve_credential ===")
v = config.resolve_credential("anysearch")
check(v is None or isinstance(v, str), f"anysearch 凭证返回正常: {type(v).__name__}")

print("\n=== 3. permission: classify ===")
check(tools.classify("read_file", {"path":"/tmp"}) == "low", "read_file = low")
check(tools.classify("search_web", {"query":"x"}) == "low", "search_web = low")
check(tools.classify("run_bash", {"command":"ls"}) == "medium", "ls = medium")
check(tools.classify("run_bash", {"command":"rm -rf /"}) == "high", "rm -rf / = high")
check(tools.classify("run_bash", {"command":"rm -rf ~"}) == "high", "rm -rf ~ = high")
check(tools.classify("run_bash", {"command":"rm -rf /tmp/build"}) == "medium", "rm -rf /tmp/build = medium (不过度拦)")
check(tools.classify("run_bash", {"command":"mkfs /dev/sda"}) == "high", "mkfs = high")

print("\n=== 4. permission: _check_permission ===")
r = tools._check_permission("read_file", {"path":"/tmp"})
check(r["decision"]=="allow" and r["risk"]=="low", "read_file 放行")
r = tools._check_permission("run_bash", {"command":"rm -rf /"})
check(r["decision"]=="deny" and r["risk"]=="high", "rm -rf / 拦截")
tools.input = make_input("y")
r = tools._check_permission("run_bash", {"command":"echo hi"})
check(r["decision"]=="allow", "medium y = 放行")
tools.input = make_input("n")
r = tools._check_permission("run_bash", {"command":"echo hi"})
check(r["decision"]=="deny", "medium n = 拒绝")

print("\n=== 5. dispatch_tool 集成 ===")
r = tools.dispatch_tool("run_bash", {"command":"rm -rf /"})
check("权限拒绝" in r, f"high 拒绝: {r}")
r = tools.dispatch_tool("read_file", {"path":"/etc/hostname"})
check(len(r)>0 and "Error" not in r, f"low 执行: {r[:30]!r}")
tools.input = make_input("n")
r = tools.dispatch_tool("run_bash", {"command":"echo hi"})
check("权限拒绝" in r, "medium n = 拒绝不执行")
tools.input = make_input("y")
r = tools.dispatch_tool("run_bash", {"command":"echo hi"})
check("权限拒绝" not in r and "Error" not in r, f"medium y = 执行: {r[:30]!r}")

print("\n=== 6. _trim_to_budget (bug 修复回归) ===")
a = Agent.__new__(Agent)
a.persona = {"system_prompt": "test"}
a.plan_mode = False
a.history = []
sys_tokens = a.estimate_tokens(a._build_messages())
a._trim_budget = sys_tokens + 30
for i in range(40):
    a.history.append({"role":"user","content":f"用户消息 {i} " * 8})
    a.history.append({"role":"assistant","content":f"回复 {i} " * 8})
messages = a._build_messages()
before = len(a.history)
a._trim_to_budget(messages)
after = len(a.history)
check(after < before, f"裁剪发生: {before} -> {after}")
check(any(m["role"]=="user" for m in a.history), "裁剪后仍保留 user 消息")
check(after >= 1, "至少保留 1 条")

print(f"\n=== {'ALL OK' if allok else 'SOME FAILED'} ===")
