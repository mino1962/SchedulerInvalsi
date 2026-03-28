import xml.etree.ElementTree as ET
import os
from typing import List, Set
from .models import Lesson, SchoolData

class XMLParser:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> SchoolData:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")

        tree = ET.parse(self.file_path)
        root = tree.getroot()

        school_data = SchoolData()

        # Iterate over all LESSON tags
        for lesson_node in root.findall('LESSON'):
            # Extract basic fields
            duration = self._get_text(lesson_node, 'DURATION')
            subject = self._get_text(lesson_node, 'SUBJECT')
            day = self._get_text(lesson_node, 'DAY')
            time = self._get_text(lesson_node, 'TIME')
            week = self._get_text(lesson_node, 'WEEK')

            # Extract lists (Teachers, Groups, Rooms)
            teachers = [t.text for t in lesson_node.findall('TEACHER') if t.text]
            groups = [g.text for g in lesson_node.findall('GROUP') if g.text]
            rooms = [r.text for r in lesson_node.findall('ROOM') if r.text]

            # Create Lesson object
            lesson = Lesson(
                id=str(id(lesson_node)), # Temporary ID
                duration=duration,
                subject=subject,
                teachers=teachers,
                groups=groups,
                rooms=rooms,
                day=day,
                time=time,
                week=week
            )
            
            school_data.lessons.append(lesson)

            # Update sets of unique values
            if subject: school_data.all_subjects.add(subject)
            school_data.all_teachers.update(teachers)
            school_data.all_groups.update(groups)
            school_data.all_rooms.update(rooms)

        return school_data

    def _get_text(self, node: ET.Element, tag: str, default: str = "") -> str:
        """Helper to safely get text content from a child node."""
        child = node.find(tag)
        return child.text if child is not None and child.text else default
