from config import get_config
import shutil , os
from openai import OpenAI
from agent import Agent , MAX_TOKENS
from persona import load_persona, list_personas
persona = load_persona("default")  #以后可以外挂到env
config = get_config()
client = OpenAI(api_key=config["API_KEY"], base_url=config["Base_URL"])
def print_separator():
    width = shutil.get_terminal_size().columns
    print("─" * width)

COMMAND_DESCRIPTIONS = {
      "exit":    "退出程序",
      "persona": "人格管理 (list/switch/current)",
      "debug":   "调试工具 (context)",
      "help":    "显示此帮助",
      "status":  "显示当前会话状态",
}
def handle_command(cmd):
    """解析命令并执行相应操作"""
    parts = cmd.split()
    action = parts[0][1:]  
    command_handlers = {
        "exit":  lambda: "exit",
        "persona":  lambda:handle_persona_command(parts),
        "debug":  lambda:handle_debug_command(parts),
        "help":  lambda:handle_help_command(), 
        "status": lambda:handle_status_command(),
    }
    if action in command_handlers:
        return command_handlers[action]()
    return None

def handle_persona_command(parts):
    if len(parts) == 1:
        print("使用list列出人格列表，使用switch <name>切换人格，使用current查看当前人格信息")
    elif parts[1] == "list":
            personas = list_personas()
            print("可用的人格列表:")
            for p in personas:
                print(f"- {p}")
    elif parts[1] == "switch":
        if len(parts) < 3:
            print("请指定要切换的人格名称")
            return
        new_persona_name = parts[2]
        try:
            global persona
            persona = load_persona(new_persona_name)
            agent.persona = persona
            print(f"已切换到人格: {new_persona_name}")
        except FileNotFoundError as e:
            print(e)
    elif parts[1] == "current":
            print(f"当前人格: {persona['name']}")
            print(f"描述: {persona['description']}")
def handle_debug_command(parts):
    action = parts[1] if len(parts) > 1 else None
    if action == None:
        if len(parts) == 1:
            print("使用context查看上次LLM发送")
    elif parts[1] == "context":
          if agent.last_messages is None:
              print("没有上次的消息记录。")
              return
          else:
            for i, msg in enumerate(agent.last_messages):
                role = msg["role"]
                preview = str(msg["content"])[:80]
                tokens = len(str(msg["content"])) // 4
                print(f"[{i}] {role}: {tokens}t | {preview}...")
            print(f"总计: {sum(len(str(m['content']))//4 for m in agent.last_messages)} tokens")
def handle_help_command():
    for cmd_name, desc in COMMAND_DESCRIPTIONS.items():
        print(f"  /{cmd_name}  {desc}")    
def handle_status_command():
    print(f"当前人格: {agent.persona['name']}")
    print(f"模型： {agent.config['Model']}")
    context_tokens = sum(len(str(m.get("content", ""))) // 4 for m in agent.history)
    print(f"{context_tokens} / {MAX_TOKENS} max tokens")
    print(f"历史消息: {len(agent.history)} 条")
    print(f"当前工作目录: {os.getcwd()}")
if __name__ == "__main__":
    agent = Agent(client, config, persona)
    while True:
        try:
            print_separator()
            cin = input("> ")
            if cin.startswith("/"):
                result = handle_command(cin)   
                if result == "exit":
                    break
                continue
            agent.chat(cin)
        except KeyboardInterrupt:
            print("\n已中断任务，输入 /exit 退出程序")
            
