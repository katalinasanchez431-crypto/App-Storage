import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import os
import json
import sys
import time
from datetime import datetime, timedelta
import csv
from tkinter import filedialog

# --- ФУНКЦІЯ ШЛЯХІВ ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- ОСНОВНИЙ КЛАС ДОДАТКА ---
class AppStorage:
    def __init__(self, root):
        self.root = root
        self.root.title("App Storage")
        self.current_dir = os.path.dirname(os.path.abspath(__file__))

        # Шлях до бази даних у Документах
        self.data_dir = os.path.join(os.path.expanduser("~"), "Documents", "AppStorageData")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self.stock_file = os.path.join(self.data_dir, "stock.json")

        # Налаштування вікна
        try:
            icon_path = resource_path("icon.ico")
            self.icon_img = ImageTk.PhotoImage(Image.open(icon_path))
            self.root.iconphoto(True, self.icon_img)
        except: pass

        self.root.attributes("-fullscreen", True)
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # Верхня панель
        self.nav_panel = tk.Frame(self.root, bg="#333333", height=60)
        self.nav_panel.pack(side="top", fill="x")

        tk.Button(self.nav_panel, text="Головна", width=15, pady=8, command=lambda: self.show_frame("MainPage")).pack(side="left", padx=5, pady=5)
        tk.Button(self.nav_panel, text="Завантажити/Керувати", width=25, pady=8, command=lambda: self.show_frame("LoadPage")).pack(side="left", padx=5, pady=5)
        tk.Button(self.nav_panel, text="Стіл (Звіти)", width=20, pady=8, command=lambda: self.show_frame("TablePage")).pack(side="left", padx=5, pady=5)
        tk.Button(self.nav_panel, text="Вихід", bg="#cc0000", fg="white", width=10, command=self.root.destroy).pack(side="right", padx=10, pady=5)

        self.status_label = tk.Label(self.nav_panel, font=("Arial", 12, "bold"), bg="#333333", fg="white")
        self.status_label.pack(side="right", padx=20)
        
        self.update_system()

        self.container = tk.Frame(self.root, highlightthickness=0, border=0)
        self.container.pack(side="top", fill="both", expand=True)

        self.frames = {}
        for PageClass in (MainPage, LoadPage, TablePage):
            page_name = PageClass.__name__
            frame = PageClass(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.place(x=0, y=0, relwidth=1, relheight=1)

        self.show_frame("MainPage")

    def update_system(self):
        now = time.strftime("%d.%m.%Y  %H:%M:%S")
        stock = self.load_stock()
        today = datetime.now().date()
        expired, warning = 0, 0
        for cat in stock.values():
            for p_name, batches in cat.items():
                for info in batches:
                    try:
                        exp_date = datetime.strptime(info['expiry'], "%d.%m.%Y").date()
                        if exp_date < today: expired += 1
                        elif exp_date <= today + timedelta(days=7): warning += 1
                    except: pass
        self.status_label.config(text=f"🔴 {expired}  |  🟡 {warning}  |  {now}")
        self.root.after(1000, self.update_system)

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        if hasattr(frame, "refresh"): frame.refresh()
        frame.tkraise()

    def get_bg(self, img_name):
        path = resource_path(img_name) 
        try:
            pil_img = Image.open(path)
            resized = pil_img.resize((self.screen_width, self.screen_height - 50), Image.LANCZOS)
            return ImageTk.PhotoImage(resized)
        except: return None

    def load_stock(self):
        if os.path.exists(self.stock_file):
            try:
                with open(self.stock_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: return {}
        return {}

    def save_stock(self, data):
        with open(self.stock_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

# --- СТОРІНКА 1: ГОЛОВНА ---
class MainPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.bg_image = controller.get_bg("StorageWall.png")
        if self.bg_image: 
            tk.Label(self, image=self.bg_image, border=0, highlightthickness=0).place(x=0, y=0, relwidth=1, relheight=1)

# --- СТОРІНКА 2: ЗАВАНТАЖЕННЯ (ВКЛАДКИ) ---
class LoadPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.bg_image = controller.get_bg("Loader.png")
        if self.bg_image: 
            tk.Label(self, image=self.bg_image, border=0, highlightthickness=0).place(x=0, y=0, relwidth=1, relheight=1)

        self.notebook = ttk.Notebook(self)
        self.notebook.place(relx=0.5, rely=0.5, anchor="center", width=700, height=600)

        # Вкладка 1: Додавання
        self.tab_add = tk.Frame(self.notebook, bg="white", padx=20, pady=20)
        self.notebook.add(self.tab_add, text="  ДОДАТИ ПАРТІЮ  ")
        self.setup_add_tab()

        # Вкладка 2: Керування
        self.tab_manage = tk.Frame(self.notebook, bg="white", padx=10, pady=10)
        self.notebook.add(self.tab_manage, text="  КЕРУВАННЯ ЗАЛИШКАМИ  ")
        
        self.scroll_area = tk.Canvas(self.tab_manage, bg="white", highlightthickness=0)
        self.inner_frame = tk.Frame(self.scroll_area, bg="white")
        self.scrollbar = tk.Scrollbar(self.tab_manage, orient="vertical", command=self.scroll_area.yview)
        self.scroll_area.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.scroll_area.pack(side="left", fill="both", expand=True)
        self.scroll_area.create_window((0,0), window=self.inner_frame, anchor="nw")
        
        tk.Button(self.tab_manage, text="ОНОВИТИ КІЛЬКІСТЬ", bg="#2196F3", fg="white", 
                  font=("Arial", 12, "bold"), pady=8, command=self.update_quantities).pack(fill="x", pady=5)

    def setup_add_tab(self):
        # Категорія (Combobox)
        tk.Label(self.tab_add, text="Категорія:", bg="white").pack()
        self.cat_combo = ttk.Combobox(self.tab_add, font=("Arial", 12), width=33)
        self.cat_combo.pack(pady=5)
        self.cat_combo.bind("<<ComboboxSelected>>", self.update_name_suggestions)

        # Назва (Combobox)
        tk.Label(self.tab_add, text="Назва товару:", bg="white").pack()
        self.name_combo = ttk.Combobox(self.tab_add, font=("Arial", 12), width=33)
        self.name_combo.pack(pady=5)

        # Інші поля
        self.add_entries = {}
        fields = [("Початкова кількість:", "qty"), ("Вжити до (ДД.ММ.РР):", "date")]
        for txt, key in fields:
            tk.Label(self.tab_add, text=txt, bg="white").pack()
            e = tk.Entry(self.tab_add, font=("Arial", 12), width=35)
            e.pack(pady=5); self.add_entries[key] = e
            if key == "qty": e.insert(0, "0")

        tk.Label(self.tab_add, text="Одиниці виміру:", bg="white").pack()
        self.unit_combo = ttk.Combobox(self.tab_add, values=["кг", "л", "од"], state="readonly", width=33)
        self.unit_combo.set("од"); self.unit_combo.pack(pady=5)

        tk.Button(self.tab_add, text="ЗБЕРЕГТИ", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                  command=self.save_new_product).pack(pady=20, fill="x")
        
        self.update_combos()

    def update_combos(self):
        stock = self.controller.load_stock()
        self.cat_combo['values'] = sorted(list(stock.keys()))

    def update_name_suggestions(self, event=None):
        stock = self.controller.load_stock()
        sel = self.cat_combo.get()
        if sel in stock: self.name_combo['values'] = sorted(list(stock[sel].keys()))

    def format_date(self, date_str):
        date_str = date_str.replace("/", ".").replace("-", ".")
        parts = date_str.split(".")
        if len(parts) != 3: return None
        d, m, y = parts
        if len(y) == 2: y = "20" + y
        try:
            valid = datetime(int(y), int(m), int(d))
            return valid.strftime("%d.%m.%Y")
        except: return None

    def save_new_product(self):
        cat = self.cat_combo.get().strip()
        name = self.name_combo.get().strip()
        qty_r = self.add_entries["qty"].get().strip()
        date_r = self.add_entries["date"].get().strip()
        unit = self.unit_combo.get()

        f_date = self.format_date(date_r)
        if not f_date: messagebox.showerror("Помилка", "Дата: ДД.ММ.РР"); return
        try: qty = int(qty_r)
        except: messagebox.showerror("Помилка", "Кількість - число"); return

        if not (cat and name): messagebox.showwarning("Помилка", "Заповніть поля!"); return

        stock = self.controller.load_stock()
        if cat not in stock: stock[cat] = {}
        if name not in stock[cat]: stock[cat][name] = []
        
        stock[cat][name].append({"qty": qty, "expiry": f_date, "unit": unit})
        self.controller.save_stock(stock)
        
        messagebox.showinfo("Успіх", f"Додано партію {name}!")
        self.update_combos()
        self.refresh()
        # Очищення полів
        self.add_entries["qty"].delete(0, tk.END); self.add_entries["qty"].insert(0, "0")
        self.add_entries["date"].delete(0, tk.END)

    def refresh(self):
        for w in self.inner_frame.winfo_children(): w.destroy()
        self.manage_entries = {}
        stock = self.controller.load_stock()
        today = datetime.now().date()

        for cat_name, products in stock.items():
            tk.Label(self.inner_frame, text=f"--- {cat_name.upper()} ---", bg="#eee", font=("Arial", 9, "bold")).pack(fill="x", pady=5)
            for p_name, batches in products.items():
                for idx, info in enumerate(batches):
                    bg_c = "white"
                    try:
                        exp = datetime.strptime(info['expiry'], "%d.%m.%Y").date()
                        if exp < today: bg_c = "#ff9999"
                        elif exp <= today + timedelta(days=7): bg_c = "#ffff99"
                    except: pass

                    row = tk.Frame(self.inner_frame, bg=bg_c)
                    row.pack(fill="x", pady=1)
                    tk.Button(row, text="✖", fg="red", bg=bg_c, relief="flat", command=lambda c=cat_name, p=p_name, i=idx: self.delete_item(c,p,i)).pack(side="left")
                    tk.Label(row, text=f"{p_name} | {info['qty']} {info.get('unit','од')} | до {info['expiry']}", bg=bg_c, width=45, anchor="w").pack(side="left")
                    ent = tk.Entry(row, width=8)
                    ent.pack(side="right", padx=5); self.manage_entries[(cat_name, p_name, idx)] = ent
        
        self.inner_frame.update_idletasks()
        self.scroll_area.config(scrollregion=self.scroll_area.bbox("all"))

    def update_quantities(self):
        stock = self.controller.load_stock()
        for (c, p, i), e in self.manage_entries.items():
            v = e.get().strip()
            if v:
                try: stock[c][p][i]["qty"] += int(v)
                except: continue
        self.controller.save_stock(stock); self.refresh()

    def delete_item(self, cat, prod, idx):
        if messagebox.askyesno("Видалення", "Видалити цю партію?"):
            stock = self.controller.load_stock()
            del stock[cat][prod][idx]
            if not stock[cat][prod]: del stock[cat][prod]
            if not stock[cat]: del stock[cat]
            self.controller.save_stock(stock); self.refresh(); self.update_combos()

# --- СТОРІНКА 3: СТІЛ (ЗВІТИ) ---
class TablePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.bg_image = controller.get_bg("TableBook.png")
        if self.bg_image: 
            tk.Label(self, image=self.bg_image, border=0, highlightthickness=0).place(x=0, y=0, relwidth=1, relheight=1)

        tk.Label(self, text="ОБЛІКОВА КНИГА", font=("Arial", 22, "bold"), bg="#fdf5e6", fg="#3e2723").pack(pady=(70, 10))
                # --- БЛОК ПОШУКУ ---
        search_frame = tk.Frame(self, bg="#fdf5e6")
        search_frame.pack(pady=5)

        tk.Label(search_frame, text="🔍 Пошук:", font=("Arial", 12, "bold"), bg="#fdf5e6").pack(side="left", padx=5)
        
        self.search_var = tk.StringVar()
        # Подія KeyRelease змушує програму шукати після кожної введеної літери
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Arial", 12), width=40)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_table) 

        # Кнопка для швидкого очищення пошуку
        tk.Button(search_frame, text="✖", command=self.clear_search, bg="#dcdcdc").pack(side="left", padx=5)

        self.table_container = tk.Frame(self, bg="white", bd=1, relief="solid")
        self.table_container.place(relx=0.5, rely=0.5, anchor="center", width=850, height=450)

        self.tree = ttk.Treeview(self.table_container, columns=("qty", "expiry"), show="tree headings")
        self.tree.heading("#0", text="📂 КАТЕГОРІЯ / ТОВАР"); self.tree.heading("qty", text="КІЛЬКІСТЬ"); self.tree.heading("expiry", text="ВЖИТИ ДО")
        self.tree.column("#0", width=400); self.tree.column("qty", width=150); self.tree.column("expiry", width=200)
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.tag_configure('warning', background='#ffff99')
        self.tree.tag_configure('expired', background='#ff9999')
        self.tree.tag_configure('category', background='#f4ece1', font=("Arial", 11, "bold"))
                # Панель інструментів під таблицею
        self.tool_panel = tk.Frame(self, bg="#fdf5e6")
        self.tool_panel.pack(pady=10)

        tk.Button(self.tool_panel, text="📥 ІМПОРТ (CSV)", bg="#795548", fg="white", 
                  command=self.import_data).pack(side="left", padx=10)
        tk.Button(self.tool_panel, text="📤 ЕКСПОРТ (Excel/CSV)", bg="#4CAF50", fg="white", 
                  command=self.export_data).pack(side="left", padx=10)
                # Кнопка очищення (червона)
        tk.Button(self.tool_panel, text="🗑️ ОЧИСТИТИ ВСЮ БАЗУ", bg="#cc0000", fg="white", 
                  command=self.clear_all_data).pack(side="left", padx=30)


    def import_data(self):
        # Вибір файлу користувачем
        file_path = filedialog.askopenfilename(
            title="Оберіть файл для імпорту",
            filetypes=[("CSV файли", "*.csv"), ("Всі файли", "*.*")]
        )
        if not file_path: return

        stock = self.controller.load_stock()
        imported_count = 0

        try:
            # utf-8-sig дозволяє Excel правильно читати кирилицю
            with open(file_path, "r", encoding="utf-8-sig") as f:
                # Вказуємо delimiter=";", бо Excel зазвичай зберігає так
                reader = csv.DictReader(f, delimiter=";")
                
                for row in reader:
                    cat = row.get('Категорія', '').strip()
                    name = row.get('Товар', '').strip()
                    qty_str = row.get('Кількість', '0').strip()
                    unit = row.get('Одиниці', 'од').strip()
                    expiry = row.get('Термін придатності', '').strip()

                    if not cat or not name: continue

                    # Валідація дати (використовуємо нашу логіку 24 -> 2024)
                    # Якщо у вас в TablePage немає методу format_date, 
                    # можна використати спрощену логіку або додати його
                    
                    if cat not in stock: stock[cat] = {}
                    if name not in stock[cat]: stock[cat][name] = []
                    
                    stock[cat][name].append({
                        "qty": int(qty_str),
                        "unit": unit,
                        "expiry": expiry
                    })
                    imported_count += 1

            self.controller.save_stock(stock)
            self.refresh()
            messagebox.showinfo("Імпорт завершено", f"Успішно додано {imported_count} записів!")
            
        except Exception as e:
            messagebox.showerror("Помилка імпорту", 
                f"Перевірте структуру файлу!\nСтовпчики: Категорія;Товар;Кількість;Одиниці;Термін придатності\nПомилка: {e}")

    def export_data(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файл", "*.csv")],
            title="Зберегти звіт як..."
        )
        if not file_path: return

        stock = self.controller.load_stock()
        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["Категорія", "Товар", "Кількість", "Одиниці", "Термін придатності"])
                
                for cat, products in stock.items():
                    for name, batches in products.items():
                        for b in batches:
                            writer.writerow([cat, name, b['qty'], b.get('unit','од'), b['expiry']])
            
            messagebox.showinfo("Експорт", "Дані збережено. Тепер їх можна відкрити в Excel або роздрукувати.")
        except Exception as e:
            messagebox.showerror("Помилка експорту", f"Не вдалося зберегти файл: {e}")

    def clear_all_data(self):
        """Повністю видаляє всі дані з подвійним підтвердженням"""
        # Перше попередження
        if messagebox.askyesno("УВАГА!", "Ви збираєтеся видалити ВСІ дані про товари та категорії.\n\nВи впевнені?"):
            
            # Друге (критичне) попередження
            if messagebox.askretrycancel("ОСТАННЄ ПОПЕРЕДЖЕННЯ", 
                                         "Дані НЕМОЖЛИВО буде відновити.\nНатисніть 'Повторити' для ВИДАЛЕННЯ або 'Скасувати' для відміни."):
                
                try:
                    # Очищуємо базу даних (записуємо порожній словник)
                    self.controller.save_stock({})
                    
                    # Оновлюємо таблицю та статус-бар
                    self.refresh()
                    messagebox.showinfo("Готово", "База даних повністю очищена.")
                except Exception as e:
                    messagebox.showerror("Помилка", f"Не вдалося очистити файл: {e}")

    def filter_table(self, event=None):
        """Фільтрує дерево товарів за введеним текстом"""
        query = self.search_var.get().lower()
        
        # Спочатку просто очищуємо таблицю і завантажуємо заново
        for item in self.tree.get_children():
            self.tree.delete(item)

        stock = self.controller.load_stock()
        today = datetime.now().date()

        for cat_name, products in stock.items():
            # Перевіряємо, чи є в цій категорії товари, що відповідають запиту
            matching_products = {}
            for p_name, batches in products.items():
                if query in p_name.lower() or query in cat_name.lower():
                    matching_products[p_name] = batches
            
            # Якщо знайшли збіги, малюємо категорію та ці товари
            if matching_products:
                cid = self.tree.insert("", "end", text=f" {cat_name.upper()}", open=True, tags=('category',))
                for p_name, batches in sorted(matching_products.items()):
                    for info in batches:
                        tag = ()
                        try:
                            exp = datetime.strptime(info['expiry'], "%d.%m.%Y").date()
                            if exp < today: tag = ('expired',)
                            elif exp <= today + timedelta(days=7): tag = ('warning',)
                        except: pass
                        
                        self.tree.insert(cid, "end", text=f"     • {p_name}", 
                                         values=(f"{info['qty']} {info.get('unit','од')}", info['expiry']), tags=tag)

    def clear_search(self):
        """Очищує поле пошуку та повертає всі дані"""
        self.search_var.set("")
        self.refresh()


    def refresh(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        stock = self.controller.load_stock()
        today = datetime.now().date()
        for cat in sorted(stock.keys()):
            cid = self.tree.insert("", "end", text=f" {cat.upper()}", open=True, tags=('category',))
            for p_name, batches in sorted(stock[cat].items()):
                for info in batches:
                    tag = ()
                    try:
                        exp = datetime.strptime(info['expiry'], "%d.%m.%Y").date()
                        if exp < today: tag = ('expired',)
                        elif exp <= today + timedelta(days=7): tag = ('warning',)
                    except: pass
                    self.tree.insert(cid, "end", text=f"     • {p_name}", 
                                     values=(f"{info['qty']} {info.get('unit','од')}", info['expiry']), tags=tag)

if __name__ == "__main__":
    root = tk.Tk()
    app = AppStorage(root)
    root.mainloop()
