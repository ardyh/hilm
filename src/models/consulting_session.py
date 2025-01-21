import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from pathlib import Path

@dataclass
class ConsultingSession:
    stage: str = "welcome"
    current_problem: Optional[str] = None
    similar_cases: Optional[Dict] = None
    framework_sections: Optional[List[Dict]] = None
    required_data: Optional[Dict] = None
    collected_data: Optional[Dict] = None
    regenerated_sections: Dict[str, str] = None
    session_id: str = None  # To identify different sessions
    
    def __post_init__(self):
        self.regenerated_sections = {}
        if not self.session_id:
            import uuid
            self.session_id = str(uuid.uuid4())
        self._ensure_data_dir()
    
    @property
    def _session_file(self) -> Path:
        """Get path to session file"""
        return Path("data/sessions") / f"session_{self.session_id}.json"
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs("data/sessions", exist_ok=True)
    
    def save(self):
        """Save session data to file"""
        state_data = asdict(self)
        with open(self._session_file, 'w') as f:
            json.dump(state_data, f)
    
    @classmethod
    def load(cls, session_id: str):
        """Load session data from file"""
        session_file = Path("data/sessions") / f"session_{session_id}.json"
        if session_file.exists():
            try:
                with open(session_file) as f:
                    data = json.load(f)
                return cls(**data)
            except Exception as e:
                print(f"Error loading session data: {str(e)}")
        return None
    
    def get_regenerated_section(self, section_key: str) -> Optional[str]:
        """Get regenerated section content"""
        return self.regenerated_sections.get(section_key)
    
    def set_regenerated_section(self, section_key: str, content: str):
        """Set regenerated section content"""
        self.regenerated_sections[section_key] = content
        self.save() 