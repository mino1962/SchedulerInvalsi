import pandas as pd
from typing import List
from .scheduler import ScheduledExam

class Exporter:
    @staticmethod
    def _prepare_data(exams: List[ScheduledExam]):
        data = []
        time_map_start = {1: "07:55", 2: "08:55", 3: "09:50", 4: "11:00", 5: "12:00", 6: "12:55"}
        time_map_end =   {1: "08:55", 2: "09:50", 3: "10:45", 4: "12:00", 5: "12:55", 6: "13:50"}
        day_trans = {"Mon": "Lunedì", "Tue": "Martedì", "Wed": "Mercoledì", "Thu": "Giovedì", "Fri": "Venerdì", "Sat": "Sabato", "Sun": "Domenica"}
        
        for e in exams:
            start_t = time_map_start.get(e.start_hour, "")
            end_t = time_map_end.get(e.end_hour, "")
            orario_str = f"{start_t}-{end_t}"
            
            row = {
                "Giorno": day_trans.get(e.day_name, e.day_name),
                "Data": e.date, # Keep as date object for sorting in DF then format
                "Classe": e.group,
                "Materia della prova": e.subject,
                "Ore": f"{e.start_hour}-{e.end_hour}",
                "Orario": orario_str,
                "Aula": e.room,
                "Docente sorveglianti": ", ".join(e.supervisors),
                "Materia Docente": "",
                "_start_hour": e.start_hour # Internal for sorting
            }
            data.append(row)
        return pd.DataFrame(data)

    @staticmethod
    def export_csv(exams: List[ScheduledExam], filepath: str):
        df = Exporter._prepare_data(exams)
        # Format date for CSV
        df['Data'] = df['Data'].apply(lambda x: x.strftime("%d/%m/%Y"))
        df.drop(columns=['_start_hour']).to_csv(filepath, index=False, sep=';', encoding='utf-8-sig')

    @staticmethod
    def export_excel(exams: List[ScheduledExam], filepath: str):
        df = Exporter._prepare_data(exams)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Foglio "cronologico": Data, Orario, Classe
            df_cron = df.sort_values(by=['Data', '_start_hour', 'Classe'])
            df_cron_out = df_cron.drop(columns=['_start_hour']).copy()
            df_cron_out['Data'] = df_cron_out['Data'].apply(lambda x: x.strftime("%d/%m/%Y"))
            df_cron_out.to_excel(writer, sheet_name='cronologico', index=False)
            
            # Foglio "Classi": Classe, Data, Orario
            df_classi = df.sort_values(by=['Classe', 'Data', '_start_hour'])
            df_classi_out = df_classi.drop(columns=['_start_hour']).copy()
            df_classi_out['Data'] = df_classi_out['Data'].apply(lambda x: x.strftime("%d/%m/%Y"))
            df_classi_out.to_excel(writer, sheet_name='Classi', index=False)
            
            # Foglio "Aule": Aula, Data, Orario, Classe
            df_aule = df.sort_values(by=['Aula', 'Data', '_start_hour', 'Classe'])
            df_aule_out = df_aule.drop(columns=['_start_hour']).copy()
            df_aule_out['Data'] = df_aule_out['Data'].apply(lambda x: x.strftime("%d/%m/%Y"))
            df_aule_out.to_excel(writer, sheet_name='Aule', index=False)
