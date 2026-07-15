import yaml , os
def load_persona(name):
    persona_path = f"personas/{name}.yaml"
    if not os.path.exists(persona_path):
        raise FileNotFoundError(f"Persona file '{persona_path}' not found.")
    with open(persona_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data
def list_personas():
    persona_dir = "personas"
    if not os.path.exists(persona_dir):
        raise FileNotFoundError(f"Persona directory '{persona_dir}' not found.")
    return [f[:-5] for f in os.listdir(persona_dir) if f.endswith(".yaml")]