from config import get_config
from openai import OpenAI
MOCK = True
class Agent:
    def __init__(self, client, config,persona):
        self.client = client
        self.config = config
        self.persona = persona
        self.history = []
        self.last_messages = None
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
              *self.history     
          ]
        message.append({"role": "user", "content": cin})
        response = self.client.chat.completions.create(
          model=self.config["Model"],
          messages=message,
          stream=True,
        )
        self.last_messages = message
        full_reply = ""
        for chunk in response:
            delta = chunk.choices[0].delta
            if  delta.reasoning_content:
                print(delta.reasoning_content, end="", flush=True)
            if delta.content:
                print(delta.content, end="", flush=True)
                full_reply += delta.content
        print()
        self.history.append({"role": "user", "content": cin})
        self.history.append({"role": "assistant", "content": full_reply})