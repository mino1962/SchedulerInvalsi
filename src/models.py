from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Lesson:
    id: str  # Unique identifier if needed, or generated
    duration: str  # e.g., "1:00", "2:00"
    subject: str
    teachers: List[str]
    groups: List[str]  # e.g., ["5BLS"]
    rooms: List[str]   # e.g., ["Palestra-02"]
    day: str           # e.g., "LUN"
    time: str          # e.g., "7:55"
    week: str          # e.g., "A"
    
    @property
    def duration_int(self) -> int:
        """Returns duration in hours (integer). Assumes format H:MM"""
        try:
            h, _ = self.duration.split(':')
            return int(h)
        except:
            return 1

    @property
    def start_slot(self) -> int:
        """Maps time string to school hour slot (1-6)."""
        time_map = {
            "7:55": 1,
            "8:55": 2,
            "9:50": 3,
            "11:00": 4,
            "12:00": 5,
            "12:55": 6,  # Sometimes represented differently?
            "13:50": 6,  # Check XML specific values
            # Add other mappings if necessary based on XML data
        }
        return time_map.get(self.time, -1)

@dataclass
class SchoolData:
    lessons: List[Lesson] = field(default_factory=list)
    all_subjects: set = field(default_factory=set)
    all_teachers: set = field(default_factory=set)
    all_groups: set = field(default_factory=set)
    all_rooms: set = field(default_factory=set)
