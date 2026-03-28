from dataclasses import dataclass, field, asdict
import json
from typing import List, Dict, Optional
import os

@dataclass
class AppConfig:
    xml_path: str = ""
    start_date: str = ""
    end_date: str = ""
    selected_classes: List[str] = field(default_factory=list)
    selected_rooms: List[str] = field(default_factory=list)
    subjects: Dict[str, int] = field(default_factory=lambda: {
        "INGLESE": 3,
        "ITALIANO": 2,
        "MATEMATICA": 2
    })
    
    allow_multiple_exams_per_day: bool = True
    allow_room_change_same_day: bool = False
    prioritize_subjects_by_hours: bool = False
    active_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5]) # 0=Mon, 5=Sat
    
    def save(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(asdict(self), f, indent=4)
            
    @classmethod
    def load(cls, filepath: str) -> 'AppConfig':
        if not os.path.exists(filepath):
            return cls()
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return cls(**data)
        except Exception as e:
            print(f"Error loading config: {e}")
            return cls()
