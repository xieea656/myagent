import os ,yaml
from dotenv import load_dotenv
from rich.console import Console
_NON_CHAT = ("asr", "tts", "voice", "embedding", "whisper")
load_dotenv()
console = Console()
with open("config.yaml", "r", encoding="utf-8") as f:
     yaml_config = yaml.safe_load(f)
default = yaml_config["default_provider"]          
provider = yaml_config["providers"][default] 
API_KEY = os.getenv(provider["api_key_env"]) 
ANYSEARCH_API_KEY = os.getenv("ANYSEARCH_API_KEY")       
if not API_KEY:
      raise ValueError(f"请在 .env 中设置 {provider['api_key_env']}")
Base_URL = provider["base_url"]
Model    = provider["default_model"]

def get_config():
    return{"API_KEY": API_KEY, "Base_URL": Base_URL, "Model": Model,"provider_name": default,}
def list_providers():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["providers"]
def get_anysearch_key():
    return ANYSEARCH_API_KEY
def switch_provider(name):
    with open("config.yaml", "r", encoding="utf-8") as f:
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

            
if __name__ == "__main__":
    config = get_config()
    console.print(config)
