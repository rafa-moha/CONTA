import customtkinter as ctk
import time
from threading import Thread

class NotificationToast(ctk.CTkToplevel):
    """ Une petite fenêtre qui apparaît, monte et disparaît """
    def __init__(self, master, message, color="green"):
        super().__init__(master)
        
        # Configuration sans bordure (style moderne)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        # Design
        if color == "green": bg = "#2ECC71"
        elif color == "red": bg = "#E74C3C"
        else: bg = "#3498DB"

        self.frame = ctk.CTkFrame(self, fg_color=bg, corner_radius=10)
        self.frame.pack(fill="both", expand=True)
        
        self.label = ctk.CTkLabel(self.frame, text=message, text_color="white", font=("Arial", 12, "bold"))
        self.label.pack(padx=20, pady=10)

        # Positionnement (Centré en bas de la fenêtre principale)
        self.update_idletasks() # Calculer la taille
        
        # On récupère la géométrie de la fenêtre parent
        parent_x = master.winfo_x()
        parent_y = master.winfo_y()
        parent_width = master.winfo_width()
        parent_height = master.winfo_height()
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        # Calcul : Centré horizontalement, en bas (80%)
        pos_x = parent_x + (parent_width // 2) - (width // 2)
        pos_y = parent_y + int(parent_height * 0.85)

        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

        # Lancer l'animation dans un thread pour ne pas bloquer l'app
        self.alpha = 1.0
        self.y_pos = pos_y
        self.animate()

    def animate(self):
        # Phase 1 : Attente visible (1.5 secondes)
        self.after(1500, self.fade_out)

    def fade_out(self):
        # Phase 2 : Disparition progressive + Montée
        if self.alpha > 0:
            self.alpha -= 0.1
            self.y_pos -= 2 # Monte de 2 pixels
            
            # Appliquer transparence (Marche sur Windows/Mac, parfois bug sur Linux)
            self.attributes("-alpha", self.alpha) 
            self.geometry(f"+{self.winfo_x()}+{self.y_pos}")
            
            self.after(50, self.fade_out) # Boucle toutes les 50ms
        else:
            self.destroy()

class LoadingOverlay(ctk.CTkToplevel):
    """ Un écran de chargement semi-transparent """
    def __init__(self, master, message="Traitement en cours..."):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-alpha", 0.9) # Semi-transparent
        
        # Centrer sur l'écran
        x = master.winfo_x() + (master.winfo_width()//2) - 150
        y = master.winfo_y() + (master.winfo_height()//2) - 75
        self.geometry(f"300x150+{x}+{y}")
        
        self.frame = ctk.CTkFrame(self, fg_color="#222", border_width=2, border_color="#555")
        self.frame.pack(fill="both", expand=True)
        
        self.lbl = ctk.CTkLabel(self.frame, text=message, font=("Arial", 14))
        self.lbl.pack(pady=(30, 20))
        
        self.progress = ctk.CTkProgressBar(self.frame, width=200, mode="indeterminate")
        self.progress.pack(pady=10)
        self.progress.start()

    def close(self):
        self.progress.stop()
        self.destroy()