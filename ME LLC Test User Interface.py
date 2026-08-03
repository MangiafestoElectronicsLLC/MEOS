# ME LLC Test User Interface 



import tkinter as tk
from tkinter import ttk, messagebox
import json, os, datetime
from fpdf import FPDF

DATA_FILE = "qc_units.json"

class QCManager:
    def __init__(self, root):
        self.root = root
        self.root.title("QC Test Manager with Serial Tracking")
        self.data = {}
        self.selected_product = ""
        self.selected_serial = ""
        self.selected_step = ""

        # Product + Serial UI
        self.product_box = ttk.Combobox(root, values=[], state="readonly", width=20)
        self.product_box.grid(row=0, column=0)
        self.product_box.bind("<<ComboboxSelected>>", self.select_product)
        ttk.Button(root, text="Add Product", command=self.add_product).grid(row=0, column=1)

        self.serial_box = ttk.Combobox(root, values=[], state="readonly", width=20)
        self.serial_box.grid(row=1, column=0)
        self.serial_box.bind("<<ComboboxSelected>>", self.select_serial)
        ttk.Button(root, text="Add Serial", command=self.add_serial).grid(row=1, column=1)

        self.step_box = ttk.Combobox(root, values=[], state="readonly", width=20)
        self.step_box.grid(row=2, column=0)
        self.step_box.bind("<<ComboboxSelected>>", self.select_step)
        ttk.Button(root, text="Add Step", command=self.add_step).grid(row=2, column=1)

        # Tasks table
        self.tree = ttk.Treeview(root, columns=("Task", "Status", "Time", "Notes", "Fails", "CAPA"), show="headings", height=10)
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.grid(row=3, column=0, columnspan=6, padx=10, pady=10)

        # Task controls
        ttk.Button(root, text="Add Task", command=self.add_task).grid(row=4, column=0)
        ttk.Button(root, text="Mark ✅", command=lambda: self.mark_task("✅")).grid(row=4, column=1)
        ttk.Button(root, text="Mark ❌", command=lambda: self.mark_task("❌")).grid(row=4, column=2)
        ttk.Button(root, text="Add Note", command=self.add_note).grid(row=4, column=3)
        ttk.Button(root, text="Flag CAPA", command=self.flag_capa).grid(row=4, column=4)

        # Save/load/export
        ttk.Button(root, text="Export Toe Tag", command=self.export_toe_tag).grid(row=5, column=0)
        ttk.Button(root, text="Save", command=self.save_data).grid(row=5, column=1)
        ttk.Button(root, text="Load", command=self.load_data).grid(row=5, column=2)
        ttk.Button(root, text="Reset", command=self.reset_status).grid(row=5, column=3)

        self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                self.data = json.load(f)
            self.product_box["values"] = list(self.data.keys())

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=2)
        messagebox.showinfo("Saved", "All data saved successfully.")

    def reset_status(self):
        if not all([self.selected_product, self.selected_serial, self.selected_step]):
            return
        for i in range(len(self.data[self.selected_product][self.selected_serial][self.selected_step])):
            self.data[self.selected_product][self.selected_serial][self.selected_step][i][1:] = ["", "", "", "0", ""]
        self.update_tree()

    def add_product(self):
        name = self.prompt("Enter Product Name")
        if name:
            self.data[name] = {}
            self.product_box["values"] = list(self.data.keys())
            self.product_box.set(name)
            self.select_product(None)

    def add_serial(self):
        if not self.selected_product: return
        sn = self.prompt("Enter Serial Number")
        if sn:
            self.data[self.selected_product][sn] = {}
            self.serial_box["values"] = list(self.data[self.selected_product].keys())
            self.serial_box.set(sn)
            self.select_serial(None)

    def add_step(self):
        if not self.selected_product or not self.selected_serial: return
        step = self.prompt("Enter Operation Step")
        if step:
            self.data[self.selected_product][self.selected_serial][step] = []
            self.step_box["values"] = list(self.data[self.selected_product][self.selected_serial].keys())
            self.step_box.set(step)
            self.select_step(None)

    def select_product(self, _):
        self.selected_product = self.product_box.get()
        serials = list(self.data[self.selected_product].keys())
        self.serial_box["values"] = serials
        self.serial_box.set("")
        self.tree.delete(*self.tree.get_children())

    def select_serial(self, _):
        self.selected_serial = self.serial_box.get()
        steps = list(self.data[self.selected_product][self.selected_serial].keys())
        self.step_box["values"] = steps
        self.step_box.set("")
        self.tree.delete(*self.tree.get_children())

    def select_step(self, _):
        self.selected_step = self.step_box.get()
        self.update_tree()

    def update_tree(self):
        self.tree.delete(*self.tree.get_children())
        if self.selected_product and self.selected_serial and self.selected_step:
            for row in self.data[self.selected_product][self.selected_serial][self.selected_step]:
                self.tree.insert("", "end", values=row)

    def add_task(self):
        if not all([self.selected_product, self.selected_serial, self.selected_step]):
            return
        task = self.prompt("Enter Task Description")
        if task:
            now = datetime.datetime.now().strftime('%H:%M')
            row = [task, "", now, "", "0", ""]
            self.data[self.selected_product][self.selected_serial][self.selected_step].append(row)
            self.update_tree()

    def mark_task(self, status):
        for item in self.tree.selection():
            idx = self.tree.index(item)
            row = self.data[self.selected_product][self.selected_serial][self.selected_step][idx]
            row[1] = status
            row[2] = datetime.datetime.now().strftime('%H:%M')
            if status == "❌":
                row[4] = str(int(row[4]) + 1)
        self.update_tree()

    def add_note(self):
        for item in self.tree.selection():
            idx = self.tree.index(item)
            note = self.prompt("Enter Note")
            self.data[self.selected_product][self.selected_serial][self.selected_step][idx][3] = note
        self.update_tree()

    def flag_capa(self):
        for item in self.tree.selection():
            idx = self.tree.index(item)
            self.data[self.selected_product][self.selected_serial][self.selected_step][idx][5] = "CAPA"
        self.update_tree()

    def prompt(self, title, default=""):
        popup = tk.Toplevel()
        popup.title(title)
        tk.Label(popup, text=title).pack(padx=10, pady=5)
        entry = tk.Entry(popup)
        entry.pack(padx=10)
        entry.insert(0, default)
        response = tk.StringVar()

        def submit():
            response.set(entry.get())
            popup.destroy()

        ttk.Button(popup, text="OK", command=submit).pack(pady=5)
        popup.grab_set()
        popup.wait_window()
        return response.get()

    def export_toe_tag(self):
        if not all([self.selected_product, self.selected_serial, self.selected_step]):
            messagebox.showerror("Missing Selection", "Select product, serial, and step.")
            return

        filename = f"ToeTag_{self.selected_product}_{self.selected_serial}_{self.selected_step}.pdf"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, f"Toe Tag - {self.selected_product}", ln=True, align="C")
        pdf.cell(200, 8, f"Serial: {self.selected_serial}", ln=True)
        pdf.cell(200, 8, f"Operation Step: {self.selected_step}", ln=True)
        pdf.cell(200, 8, f"Date:{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.ln(6)

        tasks = self.data[self.selected_product][self.selected_serial][self.selected_step]
        total = len(tasks)
        passes = sum(1 for t in tasks if t[1] == "✅")
        yield_score = round((passes / total) * 100, 2) if total else 0

        pdf.cell(200, 8, f"First Pass Yield: {yield_score}% ({passes}/{total})", ln=True)
        pdf.ln(4)

        pdf.cell(200, 8, "Task Checklist:", ln=True)
        for idx, (desc, status, time, note, fails, capa) in enumerate(tasks, 1):
            line = f"{idx}. {desc} [{status}] Time:{time} Fail:{fails}"
            if note: line += f" | Note:{note}"
            if capa: line += f" ⚠{capa}"
            pdf.cell(200, 6, line, ln=True)

        pdf.output(filename)
        messagebox.showinfo("Toe Tag Created", f"Saved as {filename}")

# 🚀 Launch the App
if __name__ == "__main__":
    root = tk.Tk()
    app = QCManager(root)
    root.mainloop()
