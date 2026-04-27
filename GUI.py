import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import math
from itertools import combinations_with_replacement
import threading
import time
import os
import sys
import csv
import webbrowser

# --- EXE RESOURCE HANDLING ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ---------------- DETAILING & SYMMETRY LOGIC ---------------- #
def is_structurally_valid(config):
    total_qty = sum(config.values())
    
    # 1. Reject odd/asymmetrical counts (except 3 for single-layer beams)
    forbidden = [1, 5, 7, 9, 11, 13, 15, 17, 19]
    if total_qty in forbidden:
        return False
    
    # 2. Symmetry check for mixed diameters
    if len(config) > 1:
        sorted_diams = sorted(config.keys(), reverse=True)
        large_bar_count = config[sorted_diams[0]]
        # Largest bars must be even (2, 4, 6...) to occupy corners/outer layers symmetrically
        if large_bar_count % 2 != 0:
            return False
            
    return True

def generate_all_solutions(required_area, max_total_bars, diameter_list, max_diff_types):
    steel_area_map = {d: (math.pi / 4) * d**2 for d in diameter_list}
    solutions = []
    
    for r in range(2, max_total_bars + 1):
        for combo in combinations_with_replacement(diameter_list, r):
            num_types = len(set(combo))
            if num_types > max_diff_types:
                continue
            
            res_config = {}
            for d in combo: res_config[d] = res_config.get(d, 0) + 1
            
            # Structural Symmetry Filter
            if not is_structurally_valid(res_config):
                continue
                
            total_area = sum(steel_area_map[d] for d in combo)
            waste = ((total_area - required_area) / required_area) * 100
            
            # 50% WASTE FILTER: Ignore designs above 50% waste
            if total_area < required_area or waste > 50.0:
                continue
            
            solutions.append({
                "qty": r, "config": res_config, "total_area": total_area,
                "waste": waste,
                "practical_score": 1 if num_types <= 2 else 0
            })
    
    # Sort primarily by waste
    solutions.sort(key=lambda x: x['waste'])
    return solutions

# ---------------- GUI CLASS ---------------- #
class NirvikSteelDesigner:
    def __init__(self, root):
        self.root = root
        self.root.title("Nirvik's Steel Estimator - Detailing Pro")
        self.root.geometry("1450x920")
        self.root.configure(bg="#f4f7f9")
        
        self.diameters = [8, 10, 12, 16, 20, 25, 28, 32]
        self.logo_path = resource_path("logo_png_nirvik.png")
        self.insta_url = "https://www.instagram.com/9nir_vik.124"
        
        try:
            icon_img = Image.open(self.logo_path)
            self.photo_icon = ImageTk.PhotoImage(icon_img)
            self.root.wm_iconphoto(True, self.photo_icon)
        except: pass

        self.current_results = []
        self.setup_ui()

    def open_insta(self, event=None):
        webbrowser.open_new(self.insta_url)

    def setup_ui(self):
        # Top Branding Header
        header = tk.Frame(self.root, bg="#0f172a", height=80)
        header.pack(fill="x")
        tk.Label(header, text="NIRVIK's STEEL ESTIMATOR - PROFESSIONAL", fg="#38bdf8", 
                 bg="#0f172a", font=("Segoe UI", 22, "bold")).pack(pady=15)

        self.container = tk.Frame(self.root, bg="#f4f7f9")
        self.container.pack(fill="both", expand=True)

        # LOADING SCREEN
        self.loading_frame = tk.Frame(self.container, bg="white")
        try:
            img_load = Image.open(self.logo_path).resize((450, 450), Image.Resampling.LANCZOS)
            self.logo_loading = ImageTk.PhotoImage(img_load)
            lbl_logo = tk.Label(self.loading_frame, image=self.logo_loading, bg="white", cursor="hand2")
            lbl_logo.pack(pady=20)
            lbl_logo.bind("<Button-1>", self.open_insta)
        except: pass

        tk.Label(self.loading_frame, text="ANALYZING SYMMETRICAL REINFORCEMENT...", font=("Segoe UI", 12), bg="white", fg="#64748b").pack()
        self.insta_btn = tk.Label(self.loading_frame, text="📸 Follow: @9nir_vik.124", font=("Segoe UI", 16, "bold"), bg="white", fg="#E1306C", cursor="hand2")
        self.insta_btn.pack(pady=10); self.insta_btn.bind("<Button-1>", self.open_insta)

        # DASHBOARD
        self.dashboard = tk.Frame(self.container, bg="#f4f7f9")
        self.dashboard.pack(fill="both", expand=True, padx=20, pady=20)

        sidebar = tk.Frame(self.dashboard, bg="white", padx=20, pady=20, highlightthickness=1, highlightbackground="#cbd5e1")
        sidebar.pack(side="left", fill="y", padx=10)

        # Input Group
        tk.Label(sidebar, text="Required Area (mm²)", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.ent_area = ttk.Entry(sidebar, font=("Segoe UI", 11)); self.ent_area.pack(fill="x", pady=(2, 12)); self.ent_area.insert(0, "1500")

        tk.Label(sidebar, text="Max Bars (Qty)", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.ent_bars = ttk.Entry(sidebar, font=("Segoe UI", 11)); self.ent_bars.pack(fill="x", pady=(2, 12)); self.ent_bars.insert(0, "12")

        tk.Label(sidebar, text="Max Diameter Varieties", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.ent_diff_types = ttk.Entry(sidebar, font=("Segoe UI", 11)); self.ent_diff_types.pack(fill="x", pady=(2, 12)); self.ent_diff_types.insert(0, "2")

        # Custom Diameters
        tk.Label(sidebar, text="--- STEEL DIAMETERS ---", bg="white", fg="#64748b", font=("Segoe UI", 9, "bold")).pack(pady=5)
        self.dia_frame = tk.Frame(sidebar, bg="white"); self.dia_frame.pack(fill="x")
        self.refresh_diameter_tags()

        add_frame = tk.Frame(sidebar, bg="white"); add_frame.pack(fill="x", pady=10)
        self.new_dia_ent = ttk.Entry(add_frame, width=8); self.new_dia_ent.pack(side="left", padx=2)
        tk.Button(add_frame, text="+", bg="#0ea5e9", fg="white", command=self.add_custom_diameter).pack(side="left")
        tk.Button(add_frame, text="CLR", bg="#ef4444", fg="white", command=self.reset_diameters, font=("Segoe UI", 8)).pack(side="left", padx=2)

        tk.Button(sidebar, text="CALCULATE", bg="#0284c7", fg="white", font=("Segoe UI", 11, "bold"), relief="flat", height=2, command=self.trigger_process).pack(fill="x", pady=(20, 5))
        self.btn_export = tk.Button(sidebar, text="SAVE CSV", bg="#16a34a", fg="white", font=("Segoe UI", 11, "bold"), relief="flat", height=2, state="disabled", command=self.export_to_csv)
        self.btn_export.pack(fill="x", pady=5)

        # Right Hand Result Layout
        res_container = tk.Frame(self.dashboard, bg="#f4f7f9")
        res_container.pack(side="left", fill="both", expand=True, padx=10)

        # Featured Box for "Structural Best"
        self.best_box = tk.LabelFrame(res_container, text=" STRUCTURALLY OPTIMIZED (SYMMETRICAL) ", font=("Segoe UI", 10, "bold"), bg="#f0f9ff", fg="#0369a1", padx=15, pady=15)
        self.best_box.pack(fill="x", pady=(0, 20))
        self.lbl_struct_best = tk.Label(self.best_box, text="No data generated yet.", bg="#f0f9ff", font=("Segoe UI", 11))
        self.lbl_struct_best.pack(anchor="w")

        # Main Table
        self.tree = ttk.Treeview(res_container, columns=("Config", "Area", "Waste"), show="headings")
        self.tree.heading("Config", text="Rebar Layout"); self.tree.heading("Area", text="Area (mm²)"); self.tree.heading("Waste", text="Waste %")
        self.tree.column("Config", width=450); self.tree.pack(fill="both", expand=True)

    def refresh_diameter_tags(self):
        for w in self.dia_frame.winfo_children(): w.destroy()
        r, c = 0, 0
        for d in sorted(self.diameters):
            tk.Label(self.dia_frame, text=f"{d}mm", bg="#f1f5f9", padx=5, pady=2).grid(row=r, column=c, padx=2, pady=2)
            c += 1
            if c > 3: c = 0; r += 1

    def add_custom_diameter(self):
        try:
            v = int(self.new_dia_ent.get())
            if v not in self.diameters: self.diameters.append(v); self.refresh_diameter_tags()
        except: pass

    def reset_diameters(self):
        self.diameters = [8, 10, 12, 16, 20, 25, 28, 32]; self.refresh_diameter_tags()

    def trigger_process(self):
        self.dashboard.pack_forget(); self.loading_frame.pack(fill="both", expand=True)
        threading.Thread(target=self.run_logic).start()

    def run_logic(self):
        try:
            req = float(self.ent_area.get())
            max_b = min(int(self.ent_bars.get()), 20)
            max_types = int(self.ent_diff_types.get())
            time.sleep(2.5) # Force loading screen visibility
            self.current_results = generate_all_solutions(req, max_b, self.diameters, max_types)
            self.root.after(0, self.update_ui)
        except: self.root.after(0, self.update_ui)

    def update_ui(self):
        self.loading_frame.pack_forget(); self.dashboard.pack(fill="both", expand=True, padx=20, pady=20)
        for i in self.tree.get_children(): self.tree.delete(i)
        
        if not self.current_results:
            self.lbl_struct_best.config(text="No designs found within 50% waste limits.")
            return

        # FEATURED OPTION: Find the "Practical" design (1-2 types) with lowest waste
        practical_results = [r for r in self.current_results if r['practical_score'] == 1]
        best_struct = practical_results[0] if practical_results else self.current_results[0]
        
        best_str = " + ".join([f"{c}x{d}mm" for d, c in sorted(best_struct['config'].items(), reverse=True)])
        self.lbl_struct_best.config(text=f"RECOMMENDED: {best_str}\nTotal Area: {best_struct['total_area']:.1f} mm² | Waste: {best_struct['waste']:.2f}%")

        # Fill main table with all valid symmetrical designs under 50% waste
        for res in self.current_results:
            c_str = " + ".join([f"{c}x{d}mm" for d, c in sorted(res['config'].items(), reverse=True)])
            self.tree.insert("", "end", values=(c_str, f"{res['total_area']:.1f}", f"{res['waste']:.2f}%"))
        
        self.btn_export.config(state="normal")

    def export_to_csv(self):
        p = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not p: return
        with open(p, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Configuration", "Area (mm2)", "Waste (%)"])
            for r in self.current_results:
                c_str = " + ".join([f"{v}x{k}mm" for k, v in sorted(r['config'].items(), reverse=True)])
                writer.writerow([c_str, f"{r['total_area']:.2f}", f"{r['waste']:.2f}"])
        messagebox.showinfo("Nirvik Export", "Design log saved successfully!")

if __name__ == "__main__":
    root = tk.Tk()
    app = NirvikSteelDesigner(root)
    root.mainloop()