import calendar
import datetime
import customtkinter as ctk

class CalendarDialog(ctk.CTkToplevel):
    def __init__(self, master, current_date: datetime.date, on_date_selected):
        super().__init__(master)
        self.title("Seleziona Data")
        self.geometry("300x300")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()
        
        self.on_date_selected = on_date_selected
        self.current_year = current_date.year
        self.current_month = current_date.month
        
        # Header
        self.frame_header = ctk.CTkFrame(self)
        self.frame_header.pack(fill="x", padx=5, pady=5)
        
        self.btn_prev = ctk.CTkButton(self.frame_header, text="<", width=30, command=self.prev_month)
        self.btn_prev.pack(side="left")
        
        self.lbl_month = ctk.CTkLabel(self.frame_header, text=f"{self.current_month}/{self.current_year}", font=("Arial", 16, "bold"))
        self.lbl_month.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(self.frame_header, text=">", width=30, command=self.next_month)
        self.btn_next.pack(side="right")
        
        # Days Grid
        self.frame_days = ctk.CTkFrame(self)
        self.frame_days.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.buttons = []
        self.render_calendar()
        
        self.focus_force()

    def render_calendar(self):
        # Clear old info
        for btn in self.buttons:
            btn.destroy()
        self.buttons = []
        
        self.lbl_month.configure(text=f"{datetime.date(self.current_year, self.current_month, 1).strftime('%B %Y')}")
        
        # Weekday headers
        days = ["Lu", "Ma", "Me", "Gi", "Ve", "Sa", "Do"]
        for i, day in enumerate(days):
            lbl = ctk.CTkLabel(self.frame_days, text=day, width=30, height=20)
            lbl.grid(row=0, column=i, padx=2, pady=2)

        # Days
        cal = calendar.Calendar()
        month_days = cal.monthdayscalendar(self.current_year, self.current_month)
        
        for r, week in enumerate(month_days):
            for c, day in enumerate(week):
                if day != 0:
                    btn = ctk.CTkButton(
                        self.frame_days, 
                        text=str(day), 
                        width=35, 
                        height=35,
                        fg_color="transparent" if c != 6 else "darkred", # Sunday red-ish
                        border_width=1,
                        text_color="white",
                        command=lambda d=day: self.select_day(d)
                    )
                    btn.grid(row=r+1, column=c, padx=2, pady=2)
                    self.buttons.append(btn)

    def prev_month(self):
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.render_calendar()

    def next_month(self):
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.render_calendar()

    def select_day(self, day):
        selected_date = datetime.date(self.current_year, self.current_month, day)
        self.on_date_selected(selected_date)
        self.destroy()
