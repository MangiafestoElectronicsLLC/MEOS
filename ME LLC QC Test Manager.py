# ME LLC QC Test Manager





import tkinter as tk
from tkinter import ttk, messagebox
import json, os, datetime
from fpdf import FPDF

DATA_FILE = "qc_test_data.json"

class QCManager:
    def __init__(self, root):
        self.root = root
        self.root.title("QC Test Manager")
        self.data = {}
        self.selected_product = ""
        self.selected_step = ""

        self.product_box = ttk.Combobox(root, values=[], state="readonly")
        self.product_box.grid(row=0, column=0)
        self.product_box.bind("<<ComboboxSelected>>", self.select_product)
        ttk.Button(root, text="Add Product", command=self.add_product).grid(row=0, column=1)

        self.step_box = ttk.Combobox(root, values=[], state="readonly")
        self.step_box.grid(row=1, column=0)
        self.step_box.bind("<<ComboboxSelected>>", self.select_step)
        ttk.Button(root, text="Add Step", command=self.add_step).grid(row=1, column=1)

        self.tree = ttk.Treeview(root, columns=("Task", "Status", "Time", "Notes", "Fails", "CAPA"), show="headings", height=10)
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        self.tree.grid(row=2, column=0, columnspan=6, padx=10, pady=10)

        ttk.Button(root, text="Add Task", command=self.add_task).grid(row=3, column=0)
        ttk.Button(root, text="Mark ✅", command=lambda: self.mark_task("✅")).grid(row=3, column=1)
        ttk.Button(root, text="Mark ❌", command=lambda: self.mark_task("❌")).grid(row=3, column=2)
        ttk.Button(root, text="Add Note", command=self.add_note).grid(row=3, column=3)
        ttk.Button(root, text="Flag CAPA", command=self.flag_capa).grid(row=3, column=4)

        ttk.Button(root, text="Export Toe Tag", command=self.export_toe_tag).grid(row=4, column=0)
        ttk.Button(root, text="Save", command=self.save_data).grid(row=4, column=1)
        ttk.Button(root, text="Load", command=self.load_data).grid(row=4, column=2)
        ttk.Button(root, text="Reset", command=self.reset_status).grid(row=4, column=3)

        self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                self.data = json.load(f)
            self.update_product_list()

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=2)
        messagebox.showinfo("Saved", "QC data saved successfully.")

    def reset_status(self):
        if not self.selected_product or not self.selected_step:
            return
        for i in range(len(self.data[self.selected_product][self.selected_step])):
            self.data[self.selected_product][self.selected_step][i][1:] = ["", "", "", "0", ""]
        self.update_tree()

    def select_product(self, _):
        self.selected_product = self.product_box.get()
        self.update_step_list()
        self.step_box.set("")
        self.tree.delete(*self.tree.get_children())

    def select_step(self, _):
        self.selected_step = self.step_box.get()
        self.update_tree()

    def update_product_list(self):
        self.product_box["values"] = list(self.data.keys())

    def update_step_list(self):
        steps = list(self.data[self.selected_product].keys()) if self.selected_product else []
        self.step_box["values"] = steps

    def update_tree(self):
        self.tree.delete(*self.tree.get_children())
        if self.selected_product and self.selected_step:
            for row in self.data[self.selected_product][self.selected_step]:
                self.tree.insert("", "end", values=row)

    def add_task(self):
        if not self.selected_product or not self.selected_step:
            return
        task = self.prompt("Enter Task Description")
        if task:
            now = datetime.datetime.now().strftime('%H:%M')
            self.data[self.selected_product][self.selected_step].append([task, "", now, "", "0", ""])
            self.update_tree()

    def mark_task(self, mark):
        for item in self.tree.selection():
            idx = self.tree.index(item)
            self.data[self.selected_product][self.selected_step][idx][1] = mark
            self.data[self.selected_product][self.selected_step][idx][2] = datetime.datetime.now().strftime('%H:%M')
            if mark == "❌":
                fails = int(self.data[self.selected_product][self.selected_step][idx][4]) + 1
                self.data[self.selected_product][self.selected_step][idx][4] = str(fails)
            self.update_tree()

    def add_note(self):
        for item in self.tree.selection():
            idx = self.tree.index(item)
            note = self.prompt("Enter QC Note")
            self.data[self.selected_product][self.selected_step][idx][3] = note
        self.update_tree()

    def flag_capa(self):
        for item in self.tree.selection():
            idx = self.tree.index(item)
            self.data[self.selected_product][self.selected_step][idx][5] = "CAPA"
        self.update_tree()

    def add_product(self):
        name = self.prompt("Enter Product Name")
        if name:
            self.data[name] = {}
            self.update_product_list()
            self.product_box.set(name)
            self.select_product(None)

    def add_step(self):
        if not self.selected_product:
            return
        step = self.prompt("Enter Op Step Number")
        if step:
            self.data[self.selected_product][step] = []
            self.update_step_list()
            self.step_box.set(step)
            self.select_step(None)

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
        if not self.selected_product or not self.selected_step:
            messagebox.showerror("Missing Selection", "Select a product and op step first.")
            return

        filename = f"ToeTag_{self.selected_product}_{self.selected_step}.pdf"
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, f"Toe Tag - {self.selected_product}", ln=True, align="C")
        pdf.cell(200, 8, f"Operation Step: {self.selected_step}", ln=True)
        pdf.cell(200, 8, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.ln(6)

        tasks = self.data[self.selected_product][self.selected_step]
        total = len(tasks)
        passes = sum(1 for t in tasks if t[1] == "✅")
        yield_score = round((passes / total) * 100, 2) if total else 0

        pdf.cell(200, 8, f"First Pass Yield: {yield_score}% ({passes}/{total})", ln=True)
        pdf.ln(4)

        pdf.cell(200, 8, "Task Checklist:", ln=True)
        for idx, (desc, status, time, note, fails, capa) in enumerate(tasks, 1):
            line = f"{idx}. {desc} [{status}] Time:{time} Fail:{fails}"
            if note: line += f" Note:{note}"
            if capa: line += f" ⚠{capa}"
            pdf.cell(200, 6, line, ln=True)

        pdf.output(filename)
        messagebox.showinfo("Toe Tag Created", f"Saved as {filename}")

# 🚀 Launch the App
if __name__ == "__main__":
    root = tk.Tk()
    app = QCManager(root)
    root.mainloop()
