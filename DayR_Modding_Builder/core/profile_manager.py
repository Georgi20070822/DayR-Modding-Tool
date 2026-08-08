import os
import json
from datetime import datetime
from .settings import SETTINGS_DIR


class ProfileManager:
    """Управление профилями проектов (хранятся в DayR_MB/profiles.json)"""

    def __init__(self):
        self.profiles_file = os.path.join(SETTINGS_DIR, "profiles.json")
        self.profiles = self.load()

    def load(self):
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save(self):
        with open(self.profiles_file, 'w', encoding='utf-8') as f:
            json.dump(self.profiles, f, indent=4, ensure_ascii=False)

    def get_profile(self, name):
        return self.profiles.get(name)

    def add_or_update(self, name, project_path, description=""):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if name in self.profiles:
            self.profiles[name]['project_path'] = project_path
            self.profiles[name]['description'] = description
            self.profiles[name]['modified'] = now
        else:
            self.profiles[name] = {
                'name': name,
                'project_path': project_path,
                'description': description,
                'created': now,
                'modified': now
            }
        self.save()
        return self.profiles[name]

    def delete(self, name):
        if name in self.profiles:
            del self.profiles[name]
            self.save()
            return True
        return False

    def get_all(self):
        return self.profiles