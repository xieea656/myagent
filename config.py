import os ,yaml
from dotenv import load_dotenv
from rich.console import Console
_NON_CHAT = ("asr", "tts", "voice", "embedding", "whisper")
load_dotenv(".xlink/.env")
console = Console()
with open(".xlink/config.yaml", "r", encoding="utf-8") as f:
     yaml_config = yaml.safe_load(f)
default = yaml_config["default_provider"]          
provider = yaml_config["providers"][default] 
API_KEY = os.getenv(provider["api_key_env"])       
if not API_KEY:
      raise ValueError(f"请在 .env 中设置 {provider['api_key_env']}")
Base_URL = provider["base_url"]
Model    = provider["default_model"]

def get_config():
    return{"API_KEY": API_KEY, "Base_URL": Base_URL, "Model": Model,"provider_name": default,"context_window": provider["context_window"]}
def list_providers():
    with open(".xlink/config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["providers"]
def switch_provider(name):
    with open(".xlink/config.yaml", "r", encoding="utf-8") as f:
        providers = yaml.safe_load(f)["providers"]
    if name not in providers:
          raise KeyError(name)
    info = providers[name]
    api_key = os.getenv(info["api_key_env"])
    if not api_key:
        raise ValueError(f"请在 .env 中设置 {info['api_key_env']}")
    return {
          "API_KEY": api_key,
          "Base_URL": info["base_url"],
          "Model": info["default_model"],
          "provider_name": name,
          "context_window": info["context_window"],
      }
def switch_model(model_name, current_config):
    new = dict(current_config)
    new["Model"] = model_name
    return new
def list_available_models(client):
    try:
        resp = client.models.list()
    except Exception:          
        return None
    ids = []                   
    for m in resp.data:        
        low = m.id.lower()
        if any(x in low for x in _NON_CHAT):   
            continue
        ids.append(m.id)       
    return sorted(ids)
def resolve_credential(name):
    """从 credentials.yaml 按名查找凭证，返回 value"""
    path = os.path.expanduser("~/.config/xlink/credentials.yaml")
    if os.path.exists(path):
        with open(path, "r") as f:
            creds = yaml.safe_load(f) or {}
        entry = creds.get(name)
        if entry:
            if entry.get("type") == "env":
                return os.getenv(entry["value"])
            return entry.get("value")
    # fallback: 检查环境变量 {NAME}_API_KEY
    return os.getenv(f"{name.upper()}_API_KEY")
def load_all_credentials():
    """返回 {name: value} 字典，供 run_bash 环境变量注入用"""
    path = os.path.expanduser("~/.config/xlink/credentials.yaml")
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        raw = yaml.safe_load(f) or {}
    result = {}
    for name, entry in raw.items():
        if isinstance(entry, dict):
            if entry.get("type") == "env":
                result[name] = os.getenv(entry["value"])
            else:
                result[name] = entry.get("value")
        else:
            result[name] = entry
    return result

def add_credential(name, value):
    """追加一个凭证"""
    path = os.path.expanduser("~/.config/xlink/credentials.yaml")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    creds = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            creds = yaml.safe_load(f) or {}
    creds[name] = {"type": "api-key", "value": value}
    with open(path, "w") as f:
        yaml.dump(creds, f, allow_unicode=True)

def remove_credential(name):
    """删除一个凭证"""
    path = os.path.expanduser("~/.config/xlink/credentials.yaml")
    if not os.path.exists(path):
        return False
    with open(path, "r") as f:
        creds = yaml.safe_load(f) or {}
    if name not in creds:
        return False
    del creds[name]
    with open(path, "w") as f:
        yaml.dump(creds, f, allow_unicode=True)
    return True

def ensure_credentials():
    """检测 credentials.yaml，不存在则交互式初始化"""
    path = os.path.expanduser("~/.config/xlink/credentials.yaml")
    if os.path.exists(path):
          return
    console.print("检测到首次运行，请配置凭证（留空=跳过/匿名）")
    anysearch_key = input("AnySearch API key (回车匿名): ").strip()
    data = {}
    if anysearch_key:
        data["anysearch"] = {"type": "api-key", "value": anysearch_key}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f)
    os.chmod(path, 0o600)
    console.print(f"凭证已保存到: {path}")
            
if __name__ == "__main__":
    config = get_config()
    console.print(config)
