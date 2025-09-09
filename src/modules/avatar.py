import yaml
from pathlib import Path

YAML_PATH = Path("brand_core/brand.yaml")

class AvatarModule:
    def __init__(self):
        self.config = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))

    def chat(self, user_input: str) -> str:
        tone = self.config["persona"]["voice"]
        return f"[{self.config['name']}] {tone}\nВопрос: {user_input}\nОтвет: пока заглушка"
