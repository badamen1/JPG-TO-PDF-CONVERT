import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
from convert_images_to_pdf import collect_images, convert_image_to_pdf, merge_images_to_pdf

class JPGToPDFGui:
    def __init__(self, root):
        self.root = root
        self.root.title("JPG to PDF Converter - Premium Edition")
        self.root.geometry("600x500")
        self.root.configure(bg="#f0f2f5")

        self.selected_files = []

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TButton", padding=6, relief="flat", background="#007bff", foreground="white", font=("Arial", 10, "bold"))
        self.style.map("TButton", background=[('active', '#0056b3')])
        
        self.style.configure("Action.TButton", padding=10, background="#28a745")
        self.style.map("Action.TButton", background=[('active', '#218838')])

        self.style.configure("Delete.TButton", padding=6, background="#dc3545")
        self.style.map("Delete.TButton", background=[('active', '#c82333')])

        self.setup_ui()

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#343a40", height=60)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text="JPG TO PDF CONVERTER", bg="#343a40", fg="white", font=("Arial", 16, "bold"), pady=15).pack()

        # Selection Buttons Frame
        btn_frame = tk.Frame(self.root, bg="#f0f2f5", pady=20)
        btn_frame.pack(fill="x")

        ttk.Button(btn_frame, text="📁 Seleccionar Imágenes", command=self.select_files).pack(side="left", padx=20)
        ttk.Button(btn_frame, text="📂 Seleccionar Carpeta", command=self.select_folder).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ Limpiar Lista", style="Delete.TButton", command=self.clear_list).pack(side="right", padx=20)

        # File Listbox with Scrollbar
        list_frame = tk.Frame(self.root, bg="#f0f2f5", padx=20)
        list_frame.pack(fill="both", expand=True)

        tk.Label(list_frame, text="Archivos Seleccionados:", bg="#f0f2f5", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.scrollbar = tk.Scrollbar(list_frame)
        self.scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(list_frame, yscrollcommand=self.scrollbar.set, font=("Arial", 9), selectmode="extended", borderwidth=0, highlightthickness=1, highlightbackground="#dee2e6")
        self.listbox.pack(fill="both", expand=True)
        self.scrollbar.config(command=self.listbox.yview)

        # Action Buttons Frame
        action_frame = tk.Frame(self.root, bg="#f8f9fa", pady=20, borderwidth=1, relief="ridge")
        action_frame.pack(fill="x")

        tk.Label(action_frame, text="La opción de borrar originales (-d) está activada por defecto", bg="#f8f9fa", fg="#6c757d", font=("Arial", 8, "italic")).pack()
        
        actions_inner = tk.Frame(action_frame, bg="#f8f9fa")
        actions_inner.pack()

        ttk.Button(actions_inner, text="✨ Combinar en un PDF", style="Action.TButton", command=self.run_merge).pack(side="left", padx=10, pady=10)
        ttk.Button(actions_inner, text="📄 Convertir Individualmente", style="Action.TButton", command=self.run_individual).pack(side="left", padx=10, pady=10)

    def select_files(self):
        files = filedialog.askopenfilenames(
            title="Seleccionar Imágenes",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png"), ("Todos los archivos", "*.*")]
        )
        if files:
            self.add_to_list(files)

    def select_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar Carpeta")
        if folder:
            images = collect_images([folder])
            self.add_to_list(images)

    def add_to_list(self, files):
        for f in files:
            abs_path = os.path.abspath(f)
            if abs_path not in self.selected_files:
                self.selected_files.append(abs_path)
                self.listbox.insert(tk.END, os.path.basename(abs_path))
        self.root.title(f"JPG to PDF Converter - {len(self.selected_files)} archivos seleccionados")

    def clear_list(self):
        self.selected_files = []
        self.listbox.delete(0, tk.END)
        self.root.title("JPG to PDF Converter")

    def run_merge(self):
        if not self.selected_files:
            messagebox.showwarning("Sin archivos", "Por favor selecciona al menos una imagen.")
            return

        # Always use 'CEDULA.pdf' in the same folder as the first image
        pdf_name = "CEDULA.pdf"
        out_dir = os.path.dirname(self.selected_files[0])

        ok, out_path = merge_images_to_pdf(self.selected_files, out_dir, pdf_name)
        
        if ok:
            # Delete originals
            for img in self.selected_files:
                try:
                    os.remove(img)
                except:
                    pass
            
            messagebox.showinfo("Éxito", f"PDF combinado creado como:\n{out_path}\n\nLos originales han sido eliminados.")
            self.clear_list()
        else:
            messagebox.showerror("Error", "Ocurrió un error al crear el PDF combinado.")

    def run_individual(self):
        if not self.selected_files:
            messagebox.showwarning("Sin archivos", "Por favor selecciona imágenes para convertir.")
            return

        # Do not ask for directory, use same as original
        out_dir = None

        success = 0
        fail = 0
        total = len(self.selected_files)

        for img in self.selected_files:
            ok, out_path = convert_image_to_pdf(img, out_dir)
            if ok:
                success += 1
                try:
                    os.remove(img)
                except:
                    pass
            else:
                fail += 1

        messagebox.showinfo("Resumen de Conversión", f"Proceso finalizado.\n\nConvertidos: {success}\nFallidos: {fail}\nTotal: {total}\n\nLos originales exitosos han sido eliminados.")
        self.clear_list()

if __name__ == "__main__":
    root = tk.Tk()
    app = JPGToPDFGui(root)
    root.mainloop()
