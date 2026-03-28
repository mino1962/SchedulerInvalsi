import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import os
import shutil
import datetime
from typing import List
from .config import AppConfig
from .parser import XMLParser
from .models import SchoolData
from .scheduler import Scheduler, ScheduledExam
from .exporter import Exporter
from .alerts import SimpleAlert

class InvalsiApp(ctk.CTk):
    def __init__(self, version="1.0"):
        super().__init__()
        self.version = version

        # Window Setup
        self.title("Invalsi Scheduler Pro")
        self.geometry("1100x700")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        # State
        self.config = AppConfig()
        self.school_data: SchoolData = None
        self.project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.upload_dir = os.path.join(self.project_dir, "upload")
        
        # Load Config on Startup
        self.load_config_initial()

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Invalsi\nScheduler", font=ctk.CTkFont(size=24, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Navigation Buttons
        self.btn_data = ctk.CTkButton(self.sidebar_frame, text="1. Dati & XML", command=self.show_frame_data)
        self.btn_data.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_config = ctk.CTkButton(self.sidebar_frame, text="2. Configurazione", command=self.show_frame_config)
        self.btn_config.grid(row=2, column=0, padx=20, pady=10)

        self.btn_export = ctk.CTkButton(self.sidebar_frame, text="3. Esporta", command=self.show_frame_export, fg_color="green", hover_color="darkgreen")
        self.btn_export.grid(row=3, column=0, padx=20, pady=10)

        self.btn_help = ctk.CTkButton(self.sidebar_frame, text="Guida / Manuale", command=self.open_manual, fg_color="gray", hover_color="darkgray")
        self.btn_help.grid(row=4, column=0, padx=20, pady=10)

        # Author Label
        self.lbl_author = ctk.CTkLabel(self.sidebar_frame, text=f"by Gelsomino Lullo\nv. {self.version}", text_color="gray", font=ctk.CTkFont(size=10))
        self.lbl_author.grid(row=5, column=0, padx=20, pady=(20, 5), sticky="s")

        self.btn_exit = ctk.CTkButton(self.sidebar_frame, text="Esci", command=self.quit_app, fg_color="red", hover_color="darkred")
        self.btn_exit.grid(row=6, column=0, padx=20, pady=(5, 20), sticky="s")

        # Main Area
        self.container = ctk.CTkFrame(self)
        self.container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        # Frames
        self.frame_data = DataView(self.container, self)
        self.frame_config = ConfigView(self.container, self)
        self.frame_export = ExportView(self.container, self)
        
        # Show Start Frame
        self.show_frame_data()
        
        # Initial Processing if config has data
        if self.config.xml_path and os.path.exists(self.config.xml_path):
            self.load_xml(self.config.xml_path, silent=True)

    def show_frame_data(self):
        self.frame_config.grid_forget()
        self.frame_export.grid_forget()
        self.frame_data.grid(row=0, column=0, sticky="nsew")

    def show_frame_config(self):
        self.frame_data.grid_forget()
        self.frame_export.grid_forget()
        self.frame_config.grid(row=0, column=0, sticky="nsew")
        self.frame_config.refresh_ui()

    def show_frame_export(self):
        self.frame_data.grid_forget()
        self.frame_config.grid_forget()
        self.frame_export.grid(row=0, column=0, sticky="nsew")

    def load_config_initial(self):
        config_path = os.path.join(self.project_dir, "config.json")
        self.config = AppConfig.load(config_path)

    def save_config(self, silent=False):
        config_path = os.path.join(self.project_dir, "config.json")
        self.config.save(config_path)
        if not silent:
            SimpleAlert(self, "Salvataggio", "Configurazione salvata con successo!")

    def load_xml(self, path, silent=False):
        try:
            parser = XMLParser(path)
            self.school_data = parser.parse()
            self.config.xml_path = path 
            self.save_config(silent=True) # Auto save path
            if not silent:
                SimpleAlert(self, "Successo", f"XML Caricato Correttamente!\nLezioni: {len(self.school_data.lessons)}")
            self.frame_data.update_status(f"File Attivo: {os.path.basename(path)}")
            if self.config.selected_classes is None:
                self.config.selected_classes = []
        except Exception as e:
            if not silent:
                SimpleAlert(self, "Errore", f"Impossibile leggere il file XML:\n{e}", is_warning=True)

    def quit_app(self):
        self.destroy()
        
    def open_manual(self):
        HelpWindow(self, self.project_dir)

class DataView(ctk.CTkFrame):
    def __init__(self, master, app: InvalsiApp):
        super().__init__(master)
        self.app = app
        
        self.lbl_title = ctk.CTkLabel(self, text="Caricamento Dati", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(pady=20)
        
        self.btn_upload = ctk.CTkButton(self, text="Carica File XML Orario", command=self.upload_file)
        self.btn_upload.pack(pady=10)
        
        # Disclaimer
        disclaimer_text = "⚠️ Il file XML deve essere generato da \"Orario Facile\" (orariofacile.com). Formati diversi non sono supportati."
        self.lbl_disclaimer = ctk.CTkLabel(self, text=disclaimer_text, text_color="orange", wraplength=550)
        self.lbl_disclaimer.pack(pady=5)
        
        self.lbl_status = ctk.CTkLabel(self, text="Nessun file caricato", text_color="gray")
        self.lbl_status.pack(pady=10)
        
        self.text_info = ctk.CTkTextbox(self, width=600, height=300)
        self.text_info.pack(pady=20)
        
    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
        if file_path:
            # Copy to upload folder
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.app.upload_dir, filename)
            try:
                shutil.copy2(file_path, dest_path)
                self.app.load_xml(dest_path)
                self.update_info()
            except Exception as e:
                SimpleAlert(self.app, "Errore Upload", str(e), is_warning=True)

    def update_status(self, text):
        self.lbl_status.configure(text=text)
        self.update_info()

    def update_info(self):
        if self.app.school_data:
            data = self.app.school_data
            info = f"--- Statistiche XML ---\n"
            info += f"Totale Lezioni: {len(data.lessons)}\n"
            info += f"Classi Trovate ({len(data.all_groups)}): {', '.join(sorted(list(data.all_groups))[:10])}...\n"
            info += f"Aule Trovate ({len(data.all_rooms)}): {', '.join(sorted(list(data.all_rooms))[:10])}...\n"
            info += f"Materie ({len(data.all_subjects)}): {', '.join(sorted(list(data.all_subjects))[:5])}...\n"
            self.text_info.delete("0.0", "end")
            self.text_info.insert("0.0", info)

class ConfigView(ctk.CTkFrame):
    def __init__(self, master, app: InvalsiApp):
        super().__init__(master)
        self.app = app
        
        self.lbl_title = ctk.CTkLabel(self, text="Configurazione Parametri", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(pady=10)
        
        # Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.tab_gen = self.tabview.add("Generale")
        self.tab_cls = self.tabview.add("Classi")
        self.tab_sub = self.tabview.add("Materie")
        self.tab_rooms = self.tabview.add("Aule")
        
        # --- Generale ---
        self.lbl_dates = ctk.CTkLabel(self.tab_gen, text="Periodo Prove (GG/MM/AAAA)", font=ctk.CTkFont(weight="bold"))
        self.lbl_dates.pack(anchor="w", pady=(10, 5))
        
        self.frame_dates = ctk.CTkFrame(self.tab_gen)
        self.frame_dates.pack(fill="x", pady=5)
        self.entry_start = ctk.CTkEntry(self.frame_dates, placeholder_text="Data Inizio")
        self.entry_start.pack(side="left", padx=5, expand=True, fill="x")
        self.entry_end = ctk.CTkEntry(self.frame_dates, placeholder_text="Data Fine")
        self.entry_end.pack(side="left", padx=5, expand=True, fill="x")
        
        # Active Days
        self.lbl_days = ctk.CTkLabel(self.tab_gen, text="Giorni Attivi (Deseleziona per saltare)", font=ctk.CTkFont(weight="bold"))
        self.lbl_days.pack(anchor="w", pady=(20, 5))
        self.frame_days = ctk.CTkFrame(self.tab_gen)
        self.frame_days.pack(fill="x")
        self.day_vars = [] 
        days_labels = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato"]
        for i, day_name in enumerate(days_labels):
            var = ctk.BooleanVar(value=True)
            chk = ctk.CTkCheckBox(self.frame_days, text=day_name, variable=var)
            chk.grid(row=0, column=i, padx=5, pady=5)
            self.day_vars.append(var)

        # Advanced
        self.lbl_adv = ctk.CTkLabel(self.tab_gen, text="Opzioni Avanzate", font=ctk.CTkFont(weight="bold"))
        self.lbl_adv.pack(anchor="w", pady=(20, 5))
        
        self.frame_adv = ctk.CTkFrame(self.tab_gen)
        self.frame_adv.pack(fill="x")
        
        self.var_multi_exam = ctk.BooleanVar(value=True)
        self.chk_multi_exam = ctk.CTkCheckBox(self.frame_adv, text="Permetti più prove al giorno (Max 2)", variable=self.var_multi_exam)
        self.chk_multi_exam.pack(anchor="w", pady=5)
        
        self.var_room_change = ctk.BooleanVar(value=False)
        self.chk_room_change = ctk.CTkCheckBox(self.frame_adv, text="Permetti cambio aula stesso giorno", variable=self.var_room_change)
        self.chk_room_change.pack(anchor="w", pady=5)

        # --- Classi (5 Colonne) ---
        self.scroll_cls = ctk.CTkScrollableFrame(self.tab_cls, label_text="Seleziona Classi")
        self.scroll_cls.pack(fill="both", expand=True)
        self.class_vars = {}

        # --- Materie ---
        self.btn_add_sub = ctk.CTkButton(self.tab_sub, text="+ Aggiungi Materia", command=self.add_subject_row)
        self.btn_add_sub.pack(pady=5)
        
        self.var_prioritize_hours = ctk.BooleanVar(value=False)
        self.chk_prioritize_hours = ctk.CTkCheckBox(self.tab_sub, text="Priorità materie con più ore (Decrescente)", variable=self.var_prioritize_hours)
        self.chk_prioritize_hours.pack(pady=5)
        
        self.scroll_sub = ctk.CTkScrollableFrame(self.tab_sub, label_text="Parametri Materie (Nome - Ore - '0' per escludere)")
        self.scroll_sub.pack(fill="both", expand=True)
        self.subject_rows = [] 
        self._init_subjects()

        # --- Aule (3 Colonne) ---
        self.scroll_rooms = ctk.CTkScrollableFrame(self.tab_rooms, label_text="Seleziona Aule")
        self.scroll_rooms.pack(fill="both", expand=True)
        self.room_vars = {}

        # Buttons (Bottom)
        self.frame_btns = ctk.CTkFrame(self)
        self.frame_btns.pack(fill="x", pady=10, side="bottom")
        self.btn_save = ctk.CTkButton(self.frame_btns, text="Salva Configurazione", command=self.save_cfg)
        self.btn_save.pack(side="left", padx=10)
        self.btn_load = ctk.CTkButton(self.frame_btns, text="Ricarica Configurazione", command=self.load_cfg)
        self.btn_load.pack(side="right", padx=10)

        self.lbl_current_config = ctk.CTkLabel(self.frame_btns, text="Config: Default (config.json)", text_color="gray")
        self.lbl_current_config.pack(side="bottom", pady=5)

    def _init_subjects(self):
        # Clear existing
        for row in self.subject_rows:
            row["frame"].destroy()
        self.subject_rows = []
        
        for sub, hours in self.app.config.subjects.items():
            self.add_subject_row(sub, hours)

    def add_subject_row(self, name="", hours=2):
        f = ctk.CTkFrame(self.scroll_sub)
        f.pack(fill="x", pady=2)
        
        # Subject name entry
        e_name = ctk.CTkEntry(f, width=250)
        e_name.insert(0, str(name))
        e_name.pack(side="left", padx=10)
        
        # Hours entry
        e_hours = ctk.CTkEntry(f, width=50)
        e_hours.insert(0, str(hours))
        e_hours.pack(side="left", padx=10)
        
        # Delete button
        btn_del = ctk.CTkButton(f, text="Elimina", width=60, fg_color="red", hover_color="darkred", 
                             command=lambda: self.remove_subject_row(f))
        btn_del.pack(side="right", padx=10)
        
        self.subject_rows.append({
            "frame": f,
            "name": e_name,
            "hours": e_hours
        })

    def remove_subject_row(self, frame):
        # Find the row by frame
        for i, row in enumerate(self.subject_rows):
            if row["frame"] == frame:
                row["frame"].destroy()
                self.subject_rows.pop(i)
                break

    def refresh_ui(self, config_path=None):
        if config_path:
            self.lbl_current_config.configure(text=f"Config: {os.path.basename(config_path)}")
        else:
            self.lbl_current_config.configure(text=f"Config: config.json (Default)")

        # Checks
        self.entry_start.delete(0, "end")
        self.entry_start.insert(0, self.app.config.start_date)
        self.entry_end.delete(0, "end")
        self.entry_end.insert(0, self.app.config.end_date)
        
        self.var_multi_exam.set(self.app.config.allow_multiple_exams_per_day)
        self.var_room_change.set(self.app.config.allow_room_change_same_day)
        self.var_prioritize_hours.set(getattr(self.app.config, 'prioritize_subjects_by_hours', False))
        
        # Days
        if hasattr(self.app.config, 'active_days'):
            active = self.app.config.active_days
            for i, var in enumerate(self.day_vars):
                # i corresponds to 0=Mon, 1=Tue...
                var.set(i in active)
        
        # Refresh Subjects
        self._init_subjects()
        
        # Checkboxes
        if self.app.school_data:
            self._populate_checkboxes_grid(self.scroll_cls, self.class_vars, self.app.school_data.all_groups, self.app.config.selected_classes, cols=5)
            self._populate_checkboxes_grid(self.scroll_rooms, self.room_vars, self.app.school_data.all_rooms, self.app.config.selected_rooms, cols=3)

    def _populate_checkboxes_grid(self, parent_frame, var_dict, all_items, selected_items, cols=1):
        for widget in parent_frame.winfo_children():
            widget.destroy()
        var_dict.clear()
        
        sorted_items = sorted(list(all_items))
        for i, item in enumerate(sorted_items):
            is_selected = item in (selected_items or [])
            var = ctk.StringVar(value=item if is_selected else "")
            
            chk = ctk.CTkCheckBox(
                parent_frame, 
                text=item, 
                variable=var, 
                onvalue=item, 
                offvalue=""
            )
            chk.grid(row=i//cols, column=i%cols, sticky="ew", padx=5, pady=2)
            if is_selected:
                chk.select()
            else:
                chk.deselect()
            var_dict[item] = chk
    
    def save_cfg(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if not filepath:
            return

        self.app.config.start_date = self.entry_start.get()
        self.app.config.end_date = self.entry_end.get()
        
        self.app.config.allow_multiple_exams_per_day = self.var_multi_exam.get()
        self.app.config.allow_room_change_same_day = self.var_room_change.get()
        self.app.config.prioritize_subjects_by_hours = self.var_prioritize_hours.get()
        
        # Save Active Days
        active = []
        for i, var in enumerate(self.day_vars):
            if var.get():
                active.append(i)
        self.app.config.active_days = active
        
        # Save Selected Classes
        selected_cls = []
        for name, chk in self.class_vars.items():
            if chk.get() == name:
                selected_cls.append(name)
        self.app.config.selected_classes = selected_cls
        
        # Save Selected Rooms
        selected_rooms = []
        for name, chk in self.room_vars.items():
            if chk.get() == name:
                selected_rooms.append(name)
        self.app.config.selected_rooms = selected_rooms
        
        # Save Subjects
        new_subjects = {}
        for row in self.subject_rows:
            name = row["name"].get().strip()
            hours_str = row["hours"].get()
            if name:
                try:
                    new_subjects[name] = int(hours_str)
                except:
                    new_subjects[name] = 0
        self.app.config.subjects = new_subjects

        self.app.config.save(filepath)
        SimpleAlert(self.app, "Salvataggio", f"Configurazione salvata in:\n{os.path.basename(filepath)}")
        self.refresh_ui(filepath)
        self.app.save_config(silent=True)

    def load_cfg(self):
        # Force focus
        self.focus_force() 
        filepath = filedialog.askopenfilename(title="Carica Configurazione", filetypes=[("JSON Files", "*.json")])
        if not filepath:
            return
            
        try:
            self.app.config = AppConfig.load(filepath)
            self.refresh_ui(filepath)
            SimpleAlert(self.app, "Caricamento", f"Caricata configurazione:\n{os.path.basename(filepath)}")
        except Exception as e:
            SimpleAlert(self.app, "Errore", f"Errore caricamento: {e}", is_warning=True)
            

class RescheduleDialog(ctk.CTkToplevel):
    def __init__(self, master, exam: ScheduledExam, scheduler: Scheduler, all_rooms: List[str], selected_rooms: List[str], on_save_callback):
        super().__init__(master)
        self.title("Modifica Prova")
        self.geometry("600x450")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        self.exam = exam
        self.scheduler = scheduler
        self.all_rooms = all_rooms
        self.selected_rooms = selected_rooms or []
        self.on_save = on_save_callback
        
        # Sort Rooms: Selected First, then Alphabetical
        other_rooms = sorted(list(set(all_rooms) - set(self.selected_rooms)))
        sorted_selected = sorted(self.selected_rooms)
        self.combined_rooms = sorted_selected + other_rooms
        
        # UI Elements
        self.lbl_info = ctk.CTkLabel(self, text=f"Modifica Prova: {exam.group} - {exam.subject}", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_info.pack(pady=10)
        
        self.frame_inputs = ctk.CTkFrame(self)
        self.frame_inputs.pack(pady=10, padx=20, fill="x")
        
        # Date
        ctk.CTkLabel(self.frame_inputs, text="Data (GG/MM/AAAA):").grid(row=0, column=0, padx=10, pady=10)
        
        self.frame_date_in = ctk.CTkFrame(self.frame_inputs, fg_color="transparent")
        self.frame_date_in.grid(row=0, column=1, padx=10, pady=10)
        
        self.entry_date = ctk.CTkEntry(self.frame_date_in, width=120)
        self.entry_date.insert(0, exam.date.strftime("%d/%m/%Y"))
        self.entry_date.pack(side="left")
        
        self.btn_cal = ctk.CTkButton(self.frame_date_in, text="📅", width=30, command=self.open_calendar)
        self.btn_cal.pack(side="left", padx=5)
        
        # Start Hour
        ctk.CTkLabel(self.frame_inputs, text="Ora Inizio (1-6):").grid(row=1, column=0, padx=10, pady=10)
        self.combo_start = ctk.CTkComboBox(self.frame_inputs, values=[str(i) for i in range(1, 7)])
        self.combo_start.set(str(exam.start_hour))
        self.combo_start.grid(row=1, column=1, padx=10, pady=10)
        
        # Room
        ctk.CTkLabel(self.frame_inputs, text="Aula:").grid(row=2, column=0, padx=10, pady=10)
        self.combo_room = ctk.CTkComboBox(self.frame_inputs, values=self.combined_rooms)
        self.combo_room.set(exam.room)
        self.combo_room.grid(row=2, column=1, padx=10, pady=10)
        
        # Status
        self.lbl_status = ctk.CTkLabel(self, text="Inserisci nuovi valori e clicca Verifica o Trova Automatico", text_color="gray")
        self.lbl_status.pack(pady=5)
        
        # Buttons
        self.frame_btns = ctk.CTkFrame(self)
        self.frame_btns.pack(pady=20, fill="x", padx=20)
        
        self.btn_check = ctk.CTkButton(self.frame_btns, text="Verifica Conflitti", command=self.check_conflicts, fg_color="orange", text_color="black")
        self.btn_check.pack(side="left", padx=10)
        
        self.btn_auto = ctk.CTkButton(self.frame_btns, text="Trova Automatico", command=self.auto_find, fg_color="blue")
        self.btn_auto.pack(side="left", padx=10)
        
        self.btn_save = ctk.CTkButton(self.frame_btns, text="Salva Modifiche", command=self.save, fg_color="green", state="disabled")
        self.btn_save.pack(side="right", padx=10)

        # Force toggle logic
        self.force_enabled = False
        
        # Modal
        self.lift()
        self.focus_force()
        self.grab_set()

    def open_calendar(self):
        try:
            curr = datetime.datetime.strptime(self.entry_date.get(), "%d/%m/%Y").date()
        except:
             curr = datetime.date.today()
        
        # Import dynamically to avoid circular import issues if placed at top level or just convention
        from .calendar_widget import CalendarDialog
        CalendarDialog(self, curr, self.set_date)

    def set_date(self, date_obj):
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, date_obj.strftime("%d/%m/%Y"))

    def check_conflicts(self):
        try:
            new_date_str = self.entry_date.get()
            new_start = int(self.combo_start.get())
            new_room = self.combo_room.get()
            
            try:
                new_date = datetime.datetime.strptime(new_date_str, "%d/%m/%Y").date()
            except ValueError:
                self.lbl_status.configure(text="Errore: Formato Data invalido!", text_color="red")
                return

            # Call logic
            errors = self.scheduler.validate_move(self.exam, new_date, new_start, new_room)
            
            if not errors:
                self.lbl_status.configure(text="Nessun conflitto rilevato! Puoi salvare.", text_color="green")
                self.btn_save.configure(state="normal", text="Salva Modifiche")
                self.force_enabled = False
            else:
                err_msg = " | ".join(errors)
                self.lbl_status.configure(text=f"CONFLITTO: {err_msg}", text_color="red")
                self.btn_save.configure(state="normal", text="Forza Salvataggio", fg_color="darkred")
                self.force_enabled = True
                
        except ValueError:
             self.lbl_status.configure(text="Errore: Ora invalida", text_color="red")

    def auto_find(self):
        result = self.scheduler.find_alternative_slot(self.exam)
        if result:
            day, start, room = result
            self.entry_date.delete(0, "end")
            self.entry_date.insert(0, day.strftime("%d/%m/%Y"))
            self.combo_start.set(str(start))
            self.combo_room.set(room)
            
            self.check_conflicts()
        else:
            self.lbl_status.configure(text="Nessuno slot libero trovato in automatico.", text_color="red")

    def save(self):
        if self.force_enabled:
             if not messagebox.askyesno("Conferma Forzatura", "Ci sono dei conflitti. Sei sicuro di voler forzare il salvataggio?"):
                 return
        
        try:
            new_date = datetime.datetime.strptime(self.entry_date.get(), "%d/%m/%Y").date()
            new_start = int(self.combo_start.get())
            new_room = self.combo_room.get()
            
            self.exam.date = new_date
            self.exam.day_name = new_date.strftime("%a")
            self.exam.start_hour = new_start
            self.exam.room = new_room
            
            current_duration = self.exam.end_hour - self.exam.start_hour + 1
            self.exam.end_hour = new_start + current_duration - 1
            
            self.on_save()
            self.destroy()
            
        except Exception as e:
            SimpleAlert(self, "Errore Salvataggio", str(e), is_warning=True)


class ExportView(ctk.CTkFrame):
    def __init__(self, master, app: InvalsiApp):
        super().__init__(master)
        self.app = app
        self.scheduler = None 
        
        self.lbl_title = ctk.CTkLabel(self, text="Esporta Calendario", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(pady=20)
        
        self.btn_run = ctk.CTkButton(self, text="Genera Scheduler", font=ctk.CTkFont(size=16), height=50, fg_color="green", hover_color="darkgreen", command=self.run_scheduler)
        self.btn_run.pack(pady=40)
        
        self.frame_results = ctk.CTkScrollableFrame(self, width=900, height=400, label_text="Risultati (Clicca su Modifica per spostare)")
        self.frame_results.pack(pady=10)
        
        self.btn_download = ctk.CTkButton(self, text="Scarica CSV/XLS", command=self.download_csv, state="disabled")
        self.btn_download.pack(pady=20)
        
    def run_scheduler(self):
        if not self.app.school_data:
            SimpleAlert(self.app, "Errore", "Dati XML non caricati!", is_warning=True)
            return
            
        for widget in self.frame_results.winfo_children():
            widget.destroy()
        
        self.scheduler = Scheduler(self.app.school_data, self.app.config)
        
        try:
            results = self.scheduler.run()
            self.refresh_results_list()
            
            # Forza l'aggiornamento della GUI per mostrare i risultati prima dell'alert
            self.app.update()
            
            if self.scheduler.errors:
                 def notify_errors():
                     SimpleAlert(self.app, "Avvisi Generazione", "\n".join(self.scheduler.errors), is_warning=True)
                 self.app.after(100, notify_errors)
                 
            if results:
                self.btn_download.configure(state="normal", fg_color="blue")
                
                # Feedback di successo se non ci sono errori critici
                if not self.scheduler.errors:
                    def notify_success():
                        SimpleAlert(self.app, "Scheduling Completato", 
                                   f"Il calendario è stato generato con successo!\n\nSelezionate {len(results)} sessioni d'esame.")
                    self.app.after(200, notify_success)
            else:
                 self.btn_download.configure(state="disabled", fg_color="gray")
                 SimpleAlert(self.app, "Attenzione", "Nessuna sessione generata. Verifica i vincoli e le classi selezionate.", is_warning=True)
                
        except Exception as e:
            SimpleAlert(self.app, "Errore Critico", f"Errore durante lo scheduling: {e}", is_warning=True)

    def refresh_results_list(self):
        for widget in self.frame_results.winfo_children():
            widget.destroy()
            
        if not self.scheduler or not self.scheduler.schedule_results:
            return

        sorted_results = sorted(self.scheduler.schedule_results, key=lambda x: (x.date, x.group))
        
        for exam in sorted_results:
            row = ctk.CTkFrame(self.frame_results)
            row.pack(fill="x", pady=2)
            
            txt = f"{exam.date.strftime('%d/%m')} ({exam.day_name}) | {exam.group} | {exam.subject} | h {exam.start_hour}-{exam.end_hour} | {exam.room}"
            lbl = ctk.CTkLabel(row, text=txt, anchor="w", width=600)
            lbl.pack(side="left", padx=10)
            
            btn_edit = ctk.CTkButton(row, text="Modifica", width=80, command=lambda e=exam: self.open_reschedule(e))
            btn_edit.pack(side="right", padx=5)

    def open_reschedule(self, exam):
        all_rooms = list(self.app.school_data.all_rooms) if self.app.school_data else []
        selected_rooms = self.app.config.selected_rooms
        
        dialog = RescheduleDialog(self.winfo_toplevel(), exam, self.scheduler, all_rooms, selected_rooms, self.refresh_results_list)

    def download_csv(self):
        if not self.scheduler or not self.scheduler.schedule_results:
            return
            
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if filepath:
            try:
                # 1. Export CSV
                Exporter.export_csv(self.scheduler.schedule_results, filepath)
                
                # 2. Export Excel (with same name but .xlsx)
                excel_path = os.path.splitext(filepath)[0] + ".xlsx"
                Exporter.export_excel(self.scheduler.schedule_results, excel_path)
                
                SimpleAlert(self.app, "Successo", f"File salvati correttamente!\nCSV: {os.path.basename(filepath)}\nExcel: {os.path.basename(excel_path)}")
            except Exception as e:
                SimpleAlert(self.app, "Errore Export", str(e), is_warning=True)

class HelpWindow(ctk.CTkToplevel):
    # Manuale integrato nel software
    MANUAL_CONTENT = """# Manuale Utente - Invalsi Scheduler Pro

## Introduzione
Invalsi Scheduler Pro è un'applicazione progettata per facilitare la creazione del calendario delle prove Invalsi, rispettando vincoli complessi come l'occupazione delle classi, dei docenti e delle aule.

## Funzionalità Principali

### 1. Caricamento Dati
- **Carica File XML Orario**: Importa il file XML generato dal software di gestione orario.
- Il software analizza automaticamente le lezioni, le classi, le aule e le materie.

⚠️ IMPORTANTE: Il file XML da cui estrarre i dati deve essere generato dal programma "Orario Facile" (sito web: https://orariofacile.com/). Se il file XML non è strutturato in questo modo, il software non potrà garantire il risultato desiderato.

### 2. Configurazione
La configurazione è organizzata in schede per una maggiore chiarezza:

#### Scheda Generale
- **Periodo Prove**: Inserisci la data di inizio e fine delle sessioni Invalsi (formato GG/MM/AAAA).
- **Giorni Attivi**: Seleziona i giorni della settimana disponibili per le prove (es. Lunedì-Venerdì).
- **Opzioni Avanzate**:
    - **Permetti più prove al giorno**: Se attivo, una classe può svolgere fino a 2 prove nello stesso giorno (es. Italiano e Matematica).
    - **Permetti cambio aula**: Se attivo, la classe può cambiare aula tra una prova e l'altra nello stesso giorno.

#### Scheda Classi
- Seleziona le classi che devono sostenere le prove. Le classi sono disposte su 5 colonne per facilitare la selezione.

#### Scheda Materie
- **Gestione Materie**: Puoi aggiungere nuove materie con il pulsante "+ Aggiungi Materia" o eliminarle con il pulsante "Elimina".
- **Modifica Nome**: Puoi modificare il nome di una materia cliccando direttamente sul campo di testo.
- **Configura Ore**: Inserisci la durata in ore per ogni prova.
- **Escludere una materia**: Imposta la durata a **0** per non pianificare quella materia.
- **Priorità Ore**: Se attivo il flag "Priorità materie con più ore", lo scheduler assegnerà prima gli slot alle materie con durata maggiore, facilitando l'incastro degli orari.

#### Scheda Aule
- Seleziona le aule informatiche da utilizzare. Le aule sono disposte su 3 colonne.

### 3. Generazione ed Esportazione
- **Genera Scheduler**: Il sistema elabora il calendario cercando di rispettare tutti i vincoli:
    - Nessuna sovrapposizione con altre lezioni della stessa classe.
    - Nessuna sovrapposizione con lezioni della stessa materia.
    - Rispetto della capienza aula (implicito se aula è libera).
    - Vincolo Presenza: l'esame viene fissato solo se la classe ha lezione in quegli orari (vengono ignorati i segnaposto come "XX" o "DISPOSIZIONE").
    - Rispetto dei giorni attivi selezionati.
- **Lista Risultati**: Visualizza tutte le prove fissate.
- **Scarica CSV/XLS**: Esporta il calendario finale in due formati:
    1. **File CSV**: Formato standard separato da punto e virgola.
    2. **File Excel (.xlsx)**: Contiene 3 fogli ottimizzati (Cronologico, per Classi, per Aule).

### 4. Modifica Manuale (Resheduling)
Dopo aver generato il calendario, puoi modificare singole prove se necessario:
1. Clicca sul pulsante **Modifica** accanto alla prova desiderata.
2. Si aprirà una finestra di dialogo.
3. Puoi cambiare manualmente **Data**, **Ora Inizio** e **Aula**.
4. Clicca su **Verifica Conflitti**: il sistema ti dirà se la nuova posizione è valida.
   - Se ci sono conflitti (es. aula occupata), apparirà un messaggio rosso.
   - Puoi scegliere di **Forzare il Salvataggio** ignorando l'avviso (a tuo rischio).
5. Oppure clicca su **Trova Automatico**: il sistema cercherà il primo slot libero disponibile.
6. Clicca su **Salva Modifiche** per confermare.

## Risoluzione Problemi
- **Il sistema non trova slot**: Prova ad allargare il periodo delle date, aggiungere più aule o abilitare le opzioni avanzate.
- **Formato Data**: Assicurati di usare GG/MM/AAAA (es. 15/03/2026).

---
### 💎 Altre Soluzioni (Versione PRO)
È disponibile un'evoluzione di questo software specifica per la generazione del calendario dei **Consigli di Classe** e degli **Scrutini**, con gestione avanzata degli orari dei docenti. Questa versione non è gratuita.

Per informazioni, contattami su GitHub: https://github.com/mino1962
---
Software by Gelsomino Lullo
"""

    def __init__(self, master, project_dir=None):
        super().__init__(master)
        self.title("Manuale Utente")
        self.geometry("800x600")
        self.attributes("-topmost", True) 
        
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.textbox = ctk.CTkTextbox(self.frame, width=780, height=580)
        self.textbox.pack(fill="both", expand=True)
        
        self.textbox.insert("0.0", self.MANUAL_CONTENT)
        self.textbox.configure(state="disabled") # Read-only
        
        self.lift()
        self.focus_force()

if __name__ == "__main__":
    app = InvalsiApp()
    app.mainloop()
