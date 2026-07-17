from config import get_config
from openai import OpenAI
import datetime, os, platform , json
MOCK = True
MAX_TOKENS = 8000
class Agent:
    def __init__(self, client, config,persona):
        self.client = client
        self.config = config
        self.persona = persona
        self.history = []
        self.last_messages = None
        self._new_session_file()
    def chat(self, cin):
        
        if MOCK:
            # 模拟流式输出：把一个字符串拆成字符，一个一个打印
            mock_text = "你好！这是一个模拟回复。"
            for char in mock_text:
                print(char, end="", flush=True)
            print()
            self.last_messages = [                    # ← 加这个
                {"role": "system", "content": self.persona["system_prompt"]},
                {"role": "user", "content": cin},
                {"role": "assistant", "content": mock_text}
            ]
            return
        message=[
                {"role": "system", "content": self.persona["system_prompt"]},
                *self.history,
                {"role": "system", "content": self.get_env_info()}
            ]
        message.append({"role": "user", "content": cin})
        while self.estimate_tokens(message) > MAX_TOKENS and len(self.history) > 0: #token超额判断
            self.history.pop(0)
            if self.history and self.history[0]["role"] != "user":
                self.history.pop(0)
            message = [{"role": "system", "content": self.persona["system_prompt"]}, *self.history
                       ,{"role": "system", "content": self.get_env_info()}]
            message.append({"role": "user", "content": cin})
        used = self.estimate_tokens(message)
        response = self.client.chat.completions.create(
            model=self.config["Model"],
            messages=message,
            stream=True,
        )
        self.last_messages = message #
        full_reply = ""
        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if getattr(delta, "reasoning_content", None):
                print(delta.reasoning_content, end="", flush=True)
            if delta.content:
                print(delta.content, end="", flush=True)
                full_reply += delta.content
        print()
        print(f"[{used} tokens]")
        self.history.append({"role": "user", "content": cin})
        self.history.append({"role": "assistant", "content": full_reply})
        with open(self.session_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({"role":"user", "content": cin}, ensure_ascii=False) + "\n") 
            f.write(json.dumps({"role":"assistant", "content": full_reply}, ensure_ascii=False) + "\n")

    def estimate_tokens(self, messages):
        """粗略估算 token 数：总字符数 / 4"""
        total_chars = sum(len(str(m.get("content", ""))) for m in messages)
        return (total_chars + 3) // 4
    def get_env_info(self):
        """获取环境信息"""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M %Z")
        cwd = os.getcwd()
        os_name = f"{platform.system()} {platform.release()}"
        return f"当前时间: {now}\n工作目录: {cwd}\n操作系统: {os_name}"
    def new_session(self):
        """开始新会话"""
        self._new_session_file()
        self.history = []

    def _new_session_file(self):
        os.makedirs("sessions", exist_ok=True)
        self.session_file = "sessions/" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".jsonl"

    def load_session(self,name):
        if name.endswith(".jsonl"):
            name = name[:-6]
        path = f"sessions/{name}.jsonl"
        with open(path, "r", encoding="utf-8") as f:
            self.history = [json.loads(line) for line in f if line.strip()]
            self.session_file = path
