"""agent的工具列表与函数集"""
TOOL_HANDLERS = {
      "read_file": read_file,
  }
TOOL_SPECS = [
      {
          "type": "function",
          "function": {
              "name": "read_file",
              "description": "读取文件的工具",          
              "parameters": {
                  "type": "object",
                  "properties": {
                      "path": {
                          "type": "string",
                          "description": "要读的文件的绝对路径,例如 '/home/xieea/coding/myagent/main.py'"
                      }
                  },
                  "required": ["path"]
              }
          }
      }
]
import os , json , subprocess
MAX_OUTPUT_CHARS = 10000
BASH_TIMEOUT = 30
def read_file(path: str, max_chars: int = MAX_OUTPUT_CHARS) -> str:
    """读文件工具"""
    if os.path.isdir(path):
        return f"Error:'{path}' 是一个目录,无法读取"
    try:
        with open(path, "rb") as f: raw = f.read()
    except FileNotFoundError:
        return f"Error:文件 '{path}' 不存在"
    except PermissionError:
        return f"Error:没有权限读取文件 '{path}'"
    except IsADirectoryError:
        return f"Error:'{path}' 是一个目录,无法读取"
    except OSError:
        return f"Error:读取文件 '{path}' 时发生错误: {OSError}"
    if b"\x00" in raw:
        return f"Error:'{path}' 是二进制文件,无法读取"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    except Exception as e:
        return f"Error:读取文件 '{path}' 时发生错误: {e} 未知的编码"
    if len(text) > max_chars: text = text[:max_chars] + f"\n\n[truncated - 显示了 {max_chars} / 共 {len(text)} 字符]"
    return text
        