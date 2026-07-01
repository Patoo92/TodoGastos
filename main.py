import sqlite3
import os
from datetime import date
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.checkbox import CheckBox
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import platform


class Database:
    def __init__(self, path):
        self.path = path
        self._init()

    def _init(self):
        conn = sqlite3.connect(self.path)
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

    def get_tareas(self, solo_pendientes=False):
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        if solo_pendientes:
            c.execute("SELECT id, texto, fecha, completada FROM tareas WHERE completada=0 ORDER BY id DESC")
        else:
            c.execute("SELECT id, texto, fecha, completada FROM tareas ORDER BY completada, id DESC")
        rows = c.fetchall()
        conn.close()
        return rows

    def add_tarea(self, texto, fecha):
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute("INSERT INTO tareas (texto, fecha, completada) VALUES (?, ?, 0)", (texto, fecha))
        conn.commit()
        conn.close()

    def toggle_tarea(self, tid):
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute("UPDATE tareas SET completada = 1 - completada WHERE id=?", (tid,))
        conn.commit()
        conn.close()

    def del_tarea(self, tid):
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute("DELETE FROM tareas WHERE id=?", (tid,))
        conn.commit()
        conn.close()

    def get_gastos(self):
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute("SELECT id, concepto, importe, fecha, categoria FROM gastos ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        return rows

    def add_gasto(self, concepto, importe, fecha, categoria):
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute("INSERT INTO gastos (concepto, importe, fecha, categoria) VALUES (?, ?, ?, ?)",
                  (concepto, importe, fecha, categoria))
        conn.commit()
        conn.close()

    def del_gasto(self, gid):
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute("DELETE FROM gastos WHERE id=?", (gid,))
        conn.commit()
        conn.close()

    def total_gastos(self):
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute("SELECT COALESCE(SUM(importe), 0) FROM gastos")
        t = c.fetchone()[0]
        conn.close()
        return t


class TareasView(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.orientation = 'vertical'
        self.filtrando = False
        self._build()

    def _build(self):
        bar = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5), padding=(dp(8), dp(4)))
        self.lbl_titulo = Label(text='Pendientes', bold=True, size_hint_x=0.5, halign='left')
        bar.add_widget(self.lbl_titulo)
        bar.add_widget(Widget())
        self.btn_filtro = Button(text='Mostrar todo', size_hint_x=0.35,
                                 background_color=(0.3, 0.3, 0.6, 1))
        self.btn_filtro.bind(on_press=self._alternar_filtro)
        bar.add_widget(self.btn_filtro)
        self.add_widget(bar)

        self.scroll = ScrollView()
        self.lista = GridLayout(cols=1, size_hint_y=None, spacing=dp(2))
        self.lista.bind(minimum_height=self.lista.setter('height'))
        self.scroll.add_widget(self.lista)
        self.add_widget(self.scroll)

        btn = Button(text='+ AÑADIR TAREA', size_hint_y=None, height=dp(50),
                     background_color=(0.2, 0.6, 0.2, 1))
        btn.bind(on_press=self._abrir_popup)
        self.add_widget(btn)

        self._recargar()

    def _alternar_filtro(self, inst):
        self.filtrando = not self.filtrando
        self.btn_filtro.text = 'Solo pendientes' if not self.filtrando else 'Mostrar todo'
        self._recargar()

    def _recargar(self):
        self.lista.clear_widgets()
        tareas = self.db.get_tareas(self.filtrando)
        pendientes = sum(1 for t in tareas if not t[3])
        self.lbl_titulo.text = f'{pendientes} pendientes' if pendientes > 0 else 'Todo al día!'

        for tid, texto, fecha, completada in tareas:
            fila = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(3), padding=(dp(6), 0))

            cb = CheckBox(active=bool(completada), size_hint_x=0.1)
            cb.bind(active=lambda inst, val, t=tid: (self.db.toggle_tarea(t), self._recargar()))
            fila.add_widget(cb)

            lbl = Label(text=texto, halign='left', valign='middle', size_hint_x=0.55)
            lbl.bind(size=lbl.setter('text_size'))
            if completada:
                lbl.color = (0.5, 0.5, 0.5, 1)
            fila.add_widget(lbl)

            fila.add_widget(Label(text=fecha, size_hint_x=0.2, color=(0.5, 0.5, 0.5, 1)))

            btn = Button(text='X', size_hint_x=0.08, background_color=(0.7, 0.1, 0.1, 1))
            btn.bind(on_press=lambda inst, t=tid: (self.db.del_tarea(t), self._recargar()))
            fila.add_widget(btn)

            self.lista.add_widget(fila)

    def _abrir_popup(self, inst):
        caja = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(15))
        caja.add_widget(Label(text='Nueva tarea', bold=True, size_hint_y=None, height=dp(30)))
        entrada = TextInput(hint_text='¿Qué hay que hacer?', multiline=False, size_hint_y=None, height=dp(42))
        caja.add_widget(entrada)
        botones = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        popup = Popup(title='', content=caja, size_hint=(0.85, 0.3))
        botones.add_widget(Button(text='Cancelar', on_press=lambda x: popup.dismiss()))
        guardar = Button(text='Guardar', background_color=(0.2, 0.6, 0.2, 1))
        guardar.bind(on_press=lambda x: self._guardar_tarea(entrada.text, popup))
        botones.add_widget(guardar)
        caja.add_widget(botones)
        popup.open()

    def _guardar_tarea(self, texto, popup):
        if texto.strip():
            self.db.add_tarea(texto.strip(), date.today().strftime('%d/%m/%Y'))
            self._recargar()
        popup.dismiss()


CAT_COLORS = {
    'Comida': (0.9, 0.6, 0.1, 1),
    'Transporte': (0.2, 0.5, 0.8, 1),
    'Casa': (0.6, 0.3, 0.7, 1),
    'Ocio': (0.2, 0.7, 0.5, 1),
    'Salud': (0.8, 0.2, 0.2, 1),
    'Otros': (0.5, 0.5, 0.5, 1),
}


class GastosView(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.orientation = 'vertical'
        self._build()

    def _build(self):
        self.scroll = ScrollView()
        self.lista = GridLayout(cols=1, size_hint_y=None, spacing=dp(2))
        self.lista.bind(minimum_height=self.lista.setter('height'))
        self.scroll.add_widget(self.lista)
        self.add_widget(self.scroll)

        self.lbl_total = Label(text='', size_hint_y=None, height=dp(36), bold=True)
        self.add_widget(self.lbl_total)

        btn = Button(text='+ AÑADIR GASTO', size_hint_y=None, height=dp(50),
                     background_color=(0.2, 0.6, 0.2, 1))
        btn.bind(on_press=self._abrir_popup)
        self.add_widget(btn)

        self._recargar()

    def _recargar(self):
        self.lista.clear_widgets()
        gastos = self.db.get_gastos()
        self.lbl_total.text = f'TOTAL: {self.db.total_gastos():.2f}EUR'

        for gid, concepto, importe, fecha, categoria in gastos:
            fila = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(3), padding=(dp(6), 0))

            color = CAT_COLORS.get(categoria, (0.5, 0.5, 0.5, 1))
            lbl_cat = Label(text=categoria, size_hint_x=0.17, color=color, bold=True)
            fila.add_widget(lbl_cat)

            lbl_con = Label(text=concepto, halign='left', valign='middle', size_hint_x=0.38)
            lbl_con.bind(size=lbl_con.setter('text_size'))
            fila.add_widget(lbl_con)

            fila.add_widget(Label(text=fecha, size_hint_x=0.18, color=(0.5, 0.5, 0.5, 1)))
            fila.add_widget(Label(text=f'{importe:.2f}EUR', size_hint_x=0.17))

            btn = Button(text='X', size_hint_x=0.08, background_color=(0.7, 0.1, 0.1, 1))
            btn.bind(on_press=lambda inst, g=gid: (self.db.del_gasto(g), self._recargar()))
            fila.add_widget(btn)

            self.lista.add_widget(fila)

    def _abrir_popup(self, inst):
        caja = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(15))
        caja.add_widget(Label(text='Nuevo gasto', bold=True, size_hint_y=None, height=dp(25)))

        entrada_con = TextInput(hint_text='Concepto', multiline=False, size_hint_y=None, height=dp(38))
        caja.add_widget(entrada_con)

        entrada_imp = TextInput(hint_text='Importe (EUR)', multiline=False, size_hint_y=None, height=dp(38))
        caja.add_widget(entrada_imp)

        spinner = Spinner(text='Categoria', values=('Comida', 'Transporte', 'Casa', 'Ocio', 'Salud', 'Otros'),
                          size_hint_y=None, height=dp(38))
        caja.add_widget(spinner)

        botones = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        popup = Popup(title='', content=caja, size_hint=(0.85, 0.42))
        botones.add_widget(Button(text='Cancelar', on_press=lambda x: popup.dismiss()))
        guardar = Button(text='Guardar', background_color=(0.2, 0.6, 0.2, 1))
        guardar.bind(on_press=lambda x: self._guardar_gasto(
            entrada_con.text, entrada_imp.text, spinner.text, popup))
        botones.add_widget(guardar)
        caja.add_widget(botones)
        popup.open()

    def _guardar_gasto(self, concepto, importe_str, categoria, popup):
        if concepto.strip() and importe_str.strip():
            try:
                importe = float(importe_str.replace(',', '.'))
                self.db.add_gasto(concepto.strip(), importe,
                                  date.today().strftime('%d/%m/%Y'), categoria)
                self._recargar()
            except ValueError:
                pass
        popup.dismiss()


class ToDoGastosApp(App):
    def build(self):
        self.title = 'To-Do & Gastos'
        if platform != 'android':
            Window.size = (420, 720)

        db_path = os.path.join(self.user_data_dir, 'todogastos.db')
        db = Database(db_path)

        tp = TabbedPanel(do_default_tab=False)
        tab1 = TabbedPanelItem(text='Tareas')
        tab1.content = TareasView(db)
        tp.add_widget(tab1)
        tab2 = TabbedPanelItem(text='Gastos')
        tab2.content = GastosView(db)
        tp.add_widget(tab2)

        if platform == 'android':
            Window.bind(on_keyboard=self._on_keyboard)

        return tp

    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:
            self.stop()
            return True
        return False


if __name__ == '__main__':
    ToDoGastosApp().run()
