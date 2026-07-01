import sqlite3
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'todogastos.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        texto TEXT NOT NULL,
        fecha TEXT NOT NULL,
        completada INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        concepto TEXT NOT NULL,
        importe REAL NOT NULL,
        fecha TEXT NOT NULL,
        categoria TEXT NOT NULL
    )""")
    conn.commit()
    conn.close()


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("To-Do & Gastos")
        self.root.geometry("500x600")
        self.root.resizable(True, True)
        self.filtrando = False

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        frame_tareas = tk.Frame(self.notebook)
        frame_gastos = tk.Frame(self.notebook)
        self.notebook.add(frame_tareas, text="Tareas")
        self.notebook.add(frame_gastos, text="Gastos")

        self._build_tareas(frame_tareas)
        self._build_gastos(frame_gastos)

        self.root.protocol("WM_DELETE_WINDOW", self._salir)
        self.root.mainloop()

    # === TAREAS ===

    def _build_tareas(self, parent):
        bar = tk.Frame(parent)
        bar.pack(fill=tk.X, padx=5, pady=5)
        self.lbl_pendientes = tk.Label(bar, text="Pendientes", font=("Segoe UI", 10, "bold"))
        self.lbl_pendientes.pack(side=tk.LEFT)
        self.btn_filtro = tk.Button(bar, text="Mostrar todo", command=self._alternar_filtro,
                                    font=("Segoe UI", 8))
        self.btn_filtro.pack(side=tk.RIGHT)

        frame_lista = tk.Frame(parent)
        frame_lista.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scroll = tk.Scrollbar(frame_lista)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.lista_tareas = tk.Listbox(frame_lista, font=("Consolas", 10),
                                       yscrollcommand=scroll.set, selectmode=tk.SINGLE,
                                       activestyle='none', borderwidth=0, highlightthickness=0)
        self.lista_tareas.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.lista_tareas.yview)
        self.lista_tareas.bind('<ButtonRelease-1>', self._click_tarea)

        tk.Button(parent, text="+ AÑADIR TAREA", font=("Segoe UI", 10, "bold"),
                  bg="#4CAF50", fg="white", command=self._add_tarea
                  ).pack(fill=tk.X, padx=5, pady=5)

        self._refrescar_tareas()

    def _alternar_filtro(self):
        self.filtrando = not self.filtrando
        self.btn_filtro.config(text="Solo pendientes" if not self.filtrando else "Mostrar todo")
        self._refrescar_tareas()

    def _refrescar_tareas(self):
        self.lista_tareas.delete(0, tk.END)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        if self.filtrando:
            c.execute("SELECT id, texto, fecha, completada FROM tareas WHERE completada=0 ORDER BY id DESC")
        else:
            c.execute("SELECT id, texto, fecha, completada FROM tareas ORDER BY completada, id DESC")
        rows = c.fetchall()
        conn.close()

        pendientes = sum(1 for r in rows if not r[3])
        self.lbl_pendientes.config(text=f"{pendientes} pendientes" if pendientes else "Todo al dia!")
        self._tareas_data = rows

        for tid, texto, fecha, completada in rows:
            marca = "[X]" if completada else "[ ]"
            display = f"{marca} {texto:<45s} {fecha}"
            self.lista_tareas.insert(tk.END, display)

    def _click_tarea(self, event):
        sel = self.lista_tareas.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._tareas_data):
            return
        tid, texto, fecha, completada = self._tareas_data[idx]

        menu = tk.Menu(self.root, tearoff=0)
        if completada:
            menu.add_command(label="Marcar como pendiente", command=lambda: self._toggle(tid))
        else:
            menu.add_command(label="Marcar como completada", command=lambda: self._toggle(tid))
        menu.add_command(label="Eliminar", command=lambda: self._eliminar_tarea(tid))
        menu.tk_popup(event.x_root, event.y_root)

    def _toggle(self, tid):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("UPDATE tareas SET completada = 1 - completada WHERE id=?", (tid,))
        conn.commit()
        conn.close()
        self._refrescar_tareas()

    def _eliminar_tarea(self, tid):
        if messagebox.askyesno("Confirmar", "Eliminar tarea?"):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM tareas WHERE id=?", (tid,))
            conn.commit()
            conn.close()
            self._refrescar_tareas()

    def _add_tarea(self):
        texto = simpledialog.askstring("Nueva tarea", "Que hay que hacer?", parent=self.root)
        if texto and texto.strip():
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO tareas (texto, fecha, completada) VALUES (?, ?, 0)",
                      (texto.strip(), date.today().strftime("%d/%m/%Y")))
            conn.commit()
            conn.close()
            self._refrescar_tareas()

    # === GASTOS ===

    CAT_COLORS = {
        'Comida': '#E67E22', 'Transporte': '#3498DB', 'Casa': '#8E44AD',
        'Ocio': '#27AE60', 'Salud': '#E74C3C', 'Otros': '#95A5A6',
    }

    def _build_gastos(self, parent):
        frame_lista = tk.Frame(parent)
        frame_lista.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ('categoria', 'concepto', 'fecha', 'importe')
        self.tree = ttk.Treeview(frame_lista, columns=columns, show='tree', selectmode='browse')
        self.tree.heading('#0', text='')
        self.tree.heading('categoria', text='Categoria')
        self.tree.heading('concepto', text='Concepto')
        self.tree.heading('fecha', text='Fecha')
        self.tree.heading('importe', text='Importe')
        self.tree.column('#0', width=0, stretch=False)
        self.tree.column('categoria', width=90)
        self.tree.column('concepto', width=180)
        self.tree.column('fecha', width=90)
        self.tree.column('importe', width=80)

        scroll = tk.Scrollbar(frame_lista, command=self.tree.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind('<ButtonRelease-1>', self._click_gasto)
        self.tree.tag_configure('odd', background='#F0F0F0')

        self.lbl_total = tk.Label(parent, text="TOTAL: 0.00EUR", font=("Segoe UI", 11, "bold"))
        self.lbl_total.pack(pady=2)

        tk.Button(parent, text="+ AÑADIR GASTO", font=("Segoe UI", 10, "bold"),
                  bg="#4CAF50", fg="white", command=self._add_gasto
                  ).pack(fill=tk.X, padx=5, pady=5)

        self._refrescar_gastos()

    def _refrescar_gastos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, concepto, importe, fecha, categoria FROM gastos ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()

        total = sum(r[2] for r in rows)
        self.lbl_total.config(text=f"TOTAL: {total:.2f}EUR")
        self._gastos_data = rows

        for i, (gid, concepto, importe, fecha, categoria) in enumerate(rows):
            cat_display = f"  {categoria}"
            tags = ('odd',) if i % 2 else ()
            self.tree.insert('', tk.END, iid=str(gid),
                             values=(cat_display, concepto, fecha, f"{importe:.2f}EUR"),
                             tags=tags)

    def _click_gasto(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        gid = int(sel[0])
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Eliminar", command=lambda: self._eliminar_gasto(gid))
        menu.tk_popup(event.x_root, event.y_root)

    def _eliminar_gasto(self, gid):
        if messagebox.askyesno("Confirmar", "Eliminar gasto?"):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("DELETE FROM gastos WHERE id=?", (gid,))
            conn.commit()
            conn.close()
            self._refrescar_gastos()

    def _add_gasto(self):
        win = tk.Toplevel(self.root)
        win.title("Nuevo gasto")
        win.geometry("350x250")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="Concepto:", font=("Segoe UI", 10)).pack(pady=(15, 2))
        entry_con = tk.Entry(win, font=("Segoe UI", 10))
        entry_con.pack(padx=20, fill=tk.X)

        tk.Label(win, text="Importe (EUR):", font=("Segoe UI", 10)).pack(pady=(10, 2))
        entry_imp = tk.Entry(win, font=("Segoe UI", 10))
        entry_imp.pack(padx=20, fill=tk.X)

        tk.Label(win, text="Categoria:", font=("Segoe UI", 10)).pack(pady=(10, 2))
        combo = ttk.Combobox(win, values=('Comida', 'Transporte', 'Casa', 'Ocio', 'Salud', 'Otros'),
                             state='readonly', font=("Segoe UI", 10))
        combo.set('Categoria')
        combo.pack(padx=20, fill=tk.X)

        def guardar():
            concepto = entry_con.get().strip()
            importe_str = entry_imp.get().strip()
            categoria = combo.get()
            if not concepto or not importe_str or categoria == 'Categoria':
                messagebox.showwarning("Campos incompletos", "Completa todos los campos", parent=win)
                return
            try:
                importe = float(importe_str.replace(',', '.'))
            except ValueError:
                messagebox.showerror("Error", "Importe invalido", parent=win)
                return
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO gastos (concepto, importe, fecha, categoria) VALUES (?, ?, ?, ?)",
                      (concepto, importe, date.today().strftime("%d/%m/%Y"), categoria))
            conn.commit()
            conn.close()
            win.destroy()
            self._refrescar_gastos()

        tk.Button(win, text="Guardar", font=("Segoe UI", 10, "bold"),
                  bg="#4CAF50", fg="white", command=guardar
                  ).pack(pady=15)

    def _salir(self):
        self.root.destroy()


if __name__ == '__main__':
    init_db()
    App()
