from config import get_config
from openai import OpenAI
from system_prompt import SYSTEM_PROMPT ,PLAN_PROMPT
import datetime, os, platform , json ,tiktoken
from tools import TOOL_SPECS, call_tool_dict,LOW_TOOL_SPECS ,TOOL_HANDLERS
from log import log_tool_call
from events import EventBus
from message import AgentMessage 
_enc = tiktoken.get_encoding("cl100k_base")
MAX_ITER = 25
class Agent:
    def __init__(self, client, config,persona):
        self.client = client
        self.config = config
        self.persona = persona
        self.history = []
        self.last_messages = None
        self._new_session_file()
        self.tools_enabled = True
        self.plan_mode = False
        self._trim_budget = config["context_window"] * 0.8
        self.events = EventBus()
    def chat(self, cin):
        user_msg = AgentMessage(role="user", content=cin)
        self.history.append(user_msg)
        self._append_jsonl(user_msg)
        last_content = ""
        for step in range(MAX_ITER):
            messages = self._build_messages()
            self._trim_to_budget(messages)
            self.last_messages = messages
            used = self.estimate_tokens(messages)
            self.events.emit("step_start",step=step+1, tokens=used)
            r = self._stream_completion(messages, self._active_tools())
            last_content = r["content"]
            asst = AgentMessage(role="assistant", content=r["content"] or "", tool_calls=r["tool_calls"])
            self.history.append(asst)
            self._append_jsonl(asst)
            if not r["tool_calls"]:
                self.events.emit("response_done", content=last_content)
                return last_content
            for call in r["tool_calls"]:
                if call["function"]["name"] == "enter_plan_mode":
                    self.plan_mode = True
                    continue
                self.events.emit("tool_call", name=call["function"]["name"], args=json.loads(call["function"]["arguments"]))
                result = call_tool_dict(call)
                self.events.emit("tool_result", name=call["function"]["name"], status="error" if result.startswith("Error:") else "success", result=result)
                tool_msg = AgentMessage(role="tool", tool_call_id=call["id"], content=result) 
                log_tool_call(
                    name = call["function"]["name"],
                    args = json.loads(call["function"]["arguments"]),
                    result = result,
                    status= "error" if result.startswith("Error:") else "success",
                )
                self.history.append(tool_msg)
                self._append_jsonl(tool_msg)
        self.events.emit("max_iter", max_iter=25)
        return last_content
    def estimate_tokens(self, messages):
        """计算token数"""
        total = 0
        for m in messages:
            content = m.content if hasattr(m, "content") else m.get("content", "")
            total += len(_enc.encode(content))
            total += 4   
        return total
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
            self.history = [AgentMessage.from_dict(json.loads(line)) for line in f if line.strip()]
            self.session_file = path
    def _stream_completion(self,messages,tools=None):
        """构造 assistant 消息"""
        kwargs = dict(model = self.config["Model"],messages=messages,stream=True)
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        response = self.client.chat.completions.create(**kwargs)
        content = ""
        tc_acc = {}
        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if getattr(delta, "reasoning_content", None):
                self.events.emit("reasoning_delta", text=delta.reasoning_content)
            if delta.content:
                self.events.emit("text_delta", text=delta.content)
                content += delta.content
            for tc in (getattr(delta, "tool_calls", None) or []):
                slot = tc_acc.setdefault(tc.index, {"id":"", "name":"", "arguments":""})
                if tc.id: slot["id"] = tc.id 
                if tc.function:
                    if tc.function.name: slot["name"] = tc.function.name
                    if tc.function.arguments: slot["arguments"] += tc.function.arguments
        tool_calls = None
        if tc_acc:
            tool_calls = [
                {"id": v["id"], "type": "function",
                "function": {"name": v["name"], "arguments": v["arguments"]}}
                for _, v in sorted(tc_acc.items())
            ]
        return {"content": content, "tool_calls": tool_calls}
    def _build_messages(self):
        messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "system", "content": self.persona["system_prompt"]},
                *[m.to_llm() for m in self.history],
                {"role": "system", "content": self.get_env_info()},
            ]
        if self.plan_mode:
            messages.insert(2, {"role": "system", "content": PLAN_PROMPT})
        return messages
    def  _append_jsonl(self, msg):
        with open(self.session_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(msg.to_dict(), ensure_ascii=False) + "\n") 
    def _active_tools(self):
        if not self.tools_enabled:
            return None                  
        if self.plan_mode:
            return LOW_TOOL_SPECS 
        return TOOL_SPECS       
    def _atomic_units(self, history):
        units = []
        i = 0
        while i < len(history):
            j = i+1
            if history[i].tool_calls:
                while j < len(history) and history[j].role == "tool":
                    j +=1
                units.append((i,j))
            else :
                units.append((i,i+1))
            i = j
        return units
    def _trim_to_budget(self, messages):
        while self.estimate_tokens(self.history) > self._trim_budget:
            units = self._atomic_units(self.history)
            if len(units) <= 1:
                break
            removed = False
            for i, (s, e) in enumerate(units):
                if i == 0:
                    remaining = self.history[e:]
                else:
                    remaining = self.history[:s] + self.history[e:]
                if any(msg.role == "user" for msg in remaining):
                    self.history = remaining
                    removed = True
                    break
            if not removed:
                break
            messages[:] = self._build_messages()
