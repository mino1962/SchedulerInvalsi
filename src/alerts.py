import customtkinter as ctk

class SimpleAlert(ctk.CTkToplevel):
    def __init__(self, master, title, message, is_warning=False):
        super().__init__(master)
        self.title(title)
        self.geometry("500x260")
        self.attributes("-topmost", True)
        self.transient(master)
        self.grab_set() 
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header_color = "#E74C3C" if is_warning else "#2ECC71"
        self.header = ctk.CTkFrame(self, fg_color=header_color, height=50, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(self.header, text="⚠️ ATTENZIONE" if is_warning else "✅ OPERAZIONE COMPLETATA", 
                     text_color="white", font=ctk.CTkFont(weight="bold", size=14)).pack(pady=12)

        self.msg_label = ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=14), wraplength=450)
        self.msg_label.grid(row=1, column=0, padx=20, pady=25, sticky="nsew")
        
        self.btn = ctk.CTkButton(self, text="HO CAPITO", command=self.destroy, width=160, height=40, font=ctk.CTkFont(weight="bold"))
        self.btn.grid(row=2, column=0, pady=(0, 25))

        # Center on master
        self.update_idletasks()
        try:
            x = master.winfo_x() + (master.winfo_width() // 2) - (500 // 2)
            y = master.winfo_y() + (master.winfo_height() // 2) - (260 // 2)
            self.geometry(f"500x260+{x}+{y}")
        except: pass
        
        self.focus_force()
