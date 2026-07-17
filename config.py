import os ,yaml
from dotenv import load_dotenv

load_dotenv()
with open("config.yaml", "r", encoding="utf-8") as f:
     yaml_config = yaml.safe_load(f)
default = yaml_config["default_provider"]          
provider = yaml_config["providers"][default] 
API_KEY = os.getenv(provider["api_key_env"])        
if not API_KEY:
      raise ValueError(f"请在 .env 中设置 {provider['api_key_env']}")
Base_URL = provider["base_url"]
Model    = provider["default_model"]

def get_config():
    return{"API_KEY": API_KEY, "Base_URL": Base_URL, "Model": Model,"provider_name": default,}
def list_providers():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["providers"]
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
if __name__ == "__main__":
    config = get_config()
    print(config)
