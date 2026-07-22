import datetime
import uuid
class AgentMessage:
    def __init__(self, role, content, tool_calls=None, tool_call_id=None,
                 id=None, timestamp=None, metadata=None):
        self.id = id or f"msg_{uuid.uuid4().hex[:8]}"       
        self.role = role                 
        self.content = content or ""      
        self.tool_calls = tool_calls      
        self.tool_call_id = tool_call_id  
        self.timestamp = timestamp or datetime.datetime.now().isoformat()
        self.metadata = metadata or {}

    def to_llm(self):
        """转成 OpenAI API 需要的 dict 格式（去掉内部字段）"""
        d = {"role": self.role, "content": self.content}
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        return d

    def to_dict(self):
        """转成完整 dict（含 id/timestamp，用于持久化）"""
        d = self.to_llm()
        d["id"] = self.id
        d["timestamp"] = self.timestamp
        return d

    @classmethod
    def from_dict(cls, data):
        """从 dict 还原 AgentMessage"""
        return cls(
            id=data.get("id"),
            role=data["role"],
            content=data.get("content", ""),
            tool_calls=data.get("tool_calls"),
            tool_call_id=data.get("tool_call_id"),
            timestamp=data.get("timestamp"),
        )