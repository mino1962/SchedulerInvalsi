from .models import SchoolData, Lesson
from .config import AppConfig
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import datetime

@dataclass
class ScheduledExam:
    date: datetime.date
    day_name: str
    start_hour: int
    end_hour: int
    subject: str
    group: str
    room: str
    supervisors: List[str] # List of strings "Name (Subject)"

class Scheduler:
    def __init__(self, data: SchoolData, config: AppConfig):
        self.data = data
        self.config = config
        self.schedule_results: List[ScheduledExam] = []
        self.errors: List[str] = []

    def get_date_range(self) -> List[datetime.date]:
        try:
            start = datetime.datetime.strptime(self.config.start_date, "%d/%m/%Y").date()
            end = datetime.datetime.strptime(self.config.end_date, "%d/%m/%Y").date()
            delta = end - start
            return [start + datetime.timedelta(days=i) for i in range(delta.days + 1)]
        except ValueError:
            self.errors.append("Formato data non valido (Usa GG/MM/AAAA)")
            return []

    def run(self) -> List[ScheduledExam]:
        days = self.get_date_range()
        if not days:
            return []
            
        # Filter active days
        days = [d for d in days if d.weekday() in self.config.active_days]
        if not days:
            self.errors.append("Nessun giorno attivo selezionato nel periodo.")
            return []

        target_classes = self.config.selected_classes
        if not target_classes:
             self.errors.append("Nessuna classe selezionata.")
             return []

        english_schedule = {d: None for d in days}
        room_usage = {d: {h: {} for h in range(1, 7)} for d in days}
        class_daily_room_lock = {} 
        class_preferred_rooms = {} 

        subjects_to_schedule = list(self.config.subjects.items())
        if getattr(self.config, 'prioritize_subjects_by_hours', False):
            # Sort by hours descending
            subjects_to_schedule.sort(key=lambda x: x[1], reverse=True)

        for cls in target_classes:
            for subj, hours in subjects_to_schedule:
                if hours <= 0: continue
                
                assigned = False
                
                for day in days:
                    if assigned: break
                    if day.weekday() == 6: continue
                    
                    exams_today = [e for e in self.schedule_results if e.group == cls and e.date == day]
                    exams_today_count = len(exams_today)
                    
                    if self.config.allow_multiple_exams_per_day:
                        if exams_today_count >= 2: continue
                    else:
                        if exams_today_count >= 1: continue
                    
                    if subj.upper() == "INGLESE" and english_schedule[day] is not None:
                        if english_schedule[day] != cls:
                            continue

                    for start_h in range(1, 7 - hours + 1):
                        end_h = start_h + hours - 1
                        slots = range(start_h, end_h + 1)
                        
                        if not self.is_class_at_school(cls, day, slots):
                            continue

                        if not self.check_class_free_for_exam(cls, day, slots, subj):
                            continue
                            
                        forced_room = class_daily_room_lock.get((day, cls))
                        preferred_for_day = None
                        
                        if forced_room:
                            if self.config.allow_room_change_same_day:
                                 preferred_for_day = forced_room
                                 forced_room = None
                            else:
                                 pass 
                        
                        preferred = class_preferred_rooms.get(cls)
                        final_preferred = preferred_for_day if preferred_for_day else preferred
                        
                        room = self._find_free_room(cls, day, slots, room_usage, forced_room, final_preferred)
                        if not room:
                            continue
                            
                        assigned = True
                        supervisors = self._find_supervisors(cls, day, slots)
                        
                        exam = ScheduledExam(
                            date=day,
                            day_name=day.strftime("%a"),
                            start_hour=start_h,
                            end_hour=end_h,
                            subject=subj,
                            group=cls,
                            room=room,
                            supervisors=supervisors
                        )
                        self.schedule_results.append(exam)
                        
                        if subj.upper() == "INGLESE":
                            english_schedule[day] = cls
                        
                        class_daily_room_lock[(day, cls)] = room
                        class_preferred_rooms[cls] = room

                        for h in slots:
                            room_usage[day][h][room] = cls
                            
                        break

        return self.schedule_results

    def validate_move(self, exam: ScheduledExam, new_date: datetime.date, new_start: int, new_room: str) -> List[str]:
        """
        Validates a proposed move. Returns a list of error messages (empty if valid).
        """
        errors = []
        duration = exam.end_hour - exam.start_hour + 1
        new_end = new_start + duration - 1
        slots = range(new_start, new_end + 1)
        
        if new_date.weekday() == 6:
            errors.append("Non puoi spostare di Domenica.")
            
        if not self.check_class_free_for_exam(exam.group, new_date, slots, exam.subject, ignore_exam=exam):
            errors.append(f"La classe {exam.group} è occupata (Lezione o altra Prova).")

        if not self.check_room_availability(new_room, new_date, slots, ignore_exam=exam):
             errors.append(f"L'aula {new_room} è occupata.")
             
        if not self.is_class_at_school(exam.group, new_date, slots):
            errors.append(f"La classe {exam.group} non ha lezione in quell'orario (non attiva a scuola).")

        return errors

    def find_alternative_slot(self, exam: ScheduledExam) -> Optional[Tuple[datetime.date, int, str]]:
        """
        Scans for the first valid slot (Date, StartHour, Room) different from current.
        """
        days = self.get_date_range()
        duration = exam.end_hour - exam.start_hour + 1
        
        start_index = 0
        try:
             start_index = days.index(exam.date)
        except:
             pass
             
        for day in days[start_index:]:
            if day.weekday() == 6: continue
            
            for start_h in range(1, 7 - duration + 1):
                end_h = start_h + duration - 1
                slots = range(start_h, end_h + 1)
                
                if not self.is_class_at_school(exam.group, day, slots):
                    continue
                    
                if not self.check_class_free_for_exam(exam.group, day, slots, exam.subject, ignore_exam=exam):
                    continue
                    
                candidates = self.config.selected_rooms if self.config.selected_rooms else sorted(list(self.data.all_rooms))
                for r in candidates:
                    # Skip exact current slot
                    if day == exam.date and start_h == exam.start_hour and r == exam.room:
                        continue

                    if self.check_room_availability(r, day, slots, ignore_exam=exam):
                        return (day, start_h, r)
        
        return None

    def is_class_at_school(self, cls: str, day: datetime.date, slots: range) -> bool:
        day_map = {0: "LUN", 1: "MAR", 2: "MER", 3: "GIO", 4: "VEN", 5: "SAB"}
        xml_day = day_map.get(day.weekday())
        if not xml_day: return False
        
        placeholders = ["XX", "DISPOSIZIONE", "DISP", "D", "-", ""]
        
        for slot_to_check in slots:
            covered = False
            for lesson in self.data.lessons:
                subj_upper = (lesson.subject or "").upper().strip()
                if subj_upper in placeholders:
                    continue

                if cls in lesson.groups and lesson.day == xml_day:
                    start = lesson.start_slot
                    if start == -1: continue
                    end = start + lesson.duration_int - 1
                    if start <= slot_to_check <= end:
                        covered = True
                        break
            if not covered:
                return False
        return True

    def is_subject_match(self, xml_subject: str, target_subject: str) -> bool:
        if not xml_subject or not target_subject:
            return False
            
        s1 = xml_subject.upper()
        t1 = target_subject.upper()
        
        if t1 in s1 or s1 in t1: return True
        if t1 == "ITALIANO" and "ITALIANA" in s1: return True
        if t1 == "MATEMATICA" and "MATEMATICA" in s1: return True
        if t1 == "INGLESE" and ("INGLESE" in s1 or "ENGLISH" in s1): return True
        if len(t1) > 3 and t1[:-1] in s1: return True
            
        return False

    def check_class_free_for_exam(self, cls, day, slots, subject, ignore_exam=None):
        for exam in self.schedule_results:
            if exam is ignore_exam: continue
            if exam.group == cls and exam.date == day:
                if (max(exam.start_hour, slots[0]) <= min(exam.end_hour, slots[-1])):
                    return False

        day_map = {0: "LUN", 1: "MAR", 2: "MER", 3: "GIO", 4: "VEN", 5: "SAB"}
        xml_day = day_map.get(day.weekday())
        if not xml_day: return False 
        
        for lesson in self.data.lessons:
            if cls in lesson.groups and lesson.day == xml_day:
                if self.is_subject_match(lesson.subject, subject):
                    les_start = lesson.start_slot
                    if les_start == -1: continue 
                    les_end = les_start + lesson.duration_int - 1
                    if (max(les_start, slots[0]) <= min(les_end, slots[-1])):
                        return False 
        return True

    def _find_supervisors(self, cls, day, slots) -> List[str]:
        supervisors_map = {} 
        day_map = {0: "LUN", 1: "MAR", 2: "MER", 3: "GIO", 4: "VEN", 5: "SAB"}
        xml_day = day_map.get(day.weekday())
        
        for lesson in self.data.lessons:
             if cls in lesson.groups and lesson.day == xml_day:
                start = lesson.start_slot
                end = start + lesson.duration_int - 1
                
                if (max(start, slots[0]) <= min(end, slots[-1])):
                     for teacher in lesson.teachers:
                        if teacher not in supervisors_map:
                             supervisors_map[teacher] = lesson.subject
        
        result = []
        for name in sorted(supervisors_map.keys()):
            subject = supervisors_map[name]
            result.append(f"{name} ({subject})")
        
        return result

    def check_room_availability(self, room, day, slots, ignore_exam=None):
        day_map = {0: "LUN", 1: "MAR", 2: "MER", 3: "GIO", 4: "VEN", 5: "SAB"}
        xml_day = day_map.get(day.weekday())
    
        for exam in self.schedule_results:
            if exam is ignore_exam: continue
            if exam.room == room and exam.date == day:
                 if (max(exam.start_hour, slots[0]) <= min(exam.end_hour, slots[-1])):
                    return False
        
        if not xml_day: return False
        for lesson in self.data.lessons:
            if room in lesson.rooms and lesson.day == xml_day:
                 les_start = lesson.start_slot
                 if les_start == -1: continue
                 les_end = les_start + lesson.duration_int - 1
                 if (max(les_start, slots[0]) <= min(les_end, slots[-1])):
                     return False
        return True

    def _find_free_room(self, cls, day, slots, room_usage, forced_room=None, preferred_room=None):
        if forced_room:
            candidates = [forced_room]
        else:
            all_rooms = self.config.selected_rooms if self.config.selected_rooms else sorted(list(self.data.all_rooms))
            if preferred_room:
                 candidates = [preferred_room] + [r for r in all_rooms if r != preferred_room]
            else:
                 candidates = all_rooms
        
        day_map = {0: "LUN", 1: "MAR", 2: "MER", 3: "GIO", 4: "VEN", 5: "SAB"}
        xml_day = day_map.get(day.weekday())
        if not xml_day: return None

        for r in candidates:
            is_free_internal = True
            for h in slots:
                if r in room_usage[day][h]:
                    is_free_internal = False
                    break
            if not is_free_internal:
                continue

            is_free_xml = True
            for lesson in self.data.lessons:
                if r in lesson.rooms and lesson.day == xml_day:
                     les_start = lesson.start_slot
                     if les_start == -1: continue
                     les_end = les_start + lesson.duration_int - 1
                     
                     if (max(les_start, slots[0]) <= min(les_end, slots[-1])):
                         is_free_xml = False
                         break
            
            if is_free_xml:
                return r
                
        return None
