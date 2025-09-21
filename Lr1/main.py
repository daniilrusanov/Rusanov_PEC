# coding: utf-8

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from datetime import datetime


# Головний клас програми, що створює та керує інтерфейсом користувача.
# Клас наслідує базовий об'єкт вікна tkinter.Tk.
class RankingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        # Конфігурація головного вікна програми.
        self.title("Інструмент для ранжування об'єктів")
        self.geometry("800x600")

        # Основний список об'єктів для сортування, що відображається користувачу.
        self.objects_list = []
        # Словник для збереження початкових індексів об'єктів.
        # Це необхідно для коректної побудови фінальної матриці.
        # Ключ: назва об'єкта, Значення: початковий індекс (0, 1, 2...).
        self.object_original_indices = {}

        # Ініціалізація та розміщення всіх елементів інтерфейсу.
        self.create_widgets()
        # Генерація початкового набору даних при запуску програми.
        self.generate_initial_objects()

    # Метод для створення та компонування всіх віджетів у головному вікні.
    def create_widgets(self):
        # --- Ліва панель для списку об'єктів та елементів керування ---
        left_frame = tk.Frame(self, padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(left_frame, text="Список об'єктів для ранжування:", font=("Arial", 12)).pack(anchor=tk.W)

        # Створення віджета Listbox для відображення об'єктів та смуги прокрутки.
        self.listbox = tk.Listbox(left_frame, selectmode=tk.SINGLE, height=15, font=("Arial", 11))
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        scrollbar = tk.Scrollbar(self.listbox, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # --- Рамка для кнопок маніпуляції списком ---
        controls_frame = tk.Frame(left_frame)
        controls_frame.pack(fill=tk.X, pady=5)

        # Кнопки "Вгору" та "Вниз" реалізують процедуру попарного порівняння.
        tk.Button(controls_frame, text="Вгору", command=self.move_up).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(controls_frame, text="Вниз", command=self.move_down).pack(side=tk.LEFT, expand=True, fill=tk.X,
                                                                            padx=5)
        tk.Button(controls_frame, text="Видалити", command=self.remove_object, bg="#ff8a80").pack(side=tk.LEFT,
                                                                                                  expand=True,
                                                                                                  fill=tk.X, padx=5)

        # --- Рамка для операцій вводу/виводу даних ---
        io_frame = tk.Frame(left_frame)
        io_frame.pack(fill=tk.X, pady=10)

        tk.Button(io_frame, text="Згенерувати об'єкти", command=self.generate_initial_objects).pack(side=tk.LEFT,
                                                                                                    expand=True,
                                                                                                    fill=tk.X, padx=5)
        tk.Button(io_frame, text="Завантажити з файлу", command=self.load_from_file).pack(side=tk.LEFT, expand=True,
                                                                                          fill=tk.X, padx=5)
        tk.Button(io_frame, text="Додати вручну", command=self.add_manually).pack(side=tk.LEFT, expand=True, fill=tk.X,
                                                                                  padx=5)

        # --- Кнопка для завершення ранжування та збереження результату ---
        tk.Button(left_frame, text="Завершити та зберегти матрицю", command=self.save_matrix, bg="#80c8ff",
                  font=("Arial", 12, "bold")).pack(fill=tk.X, pady=20)

        # --- Права панель для протоколу дій експерта ---
        right_frame = tk.Frame(self, padx=10, pady=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        tk.Label(right_frame, text="Протокол дій:", font=("Arial", 12)).pack(anchor=tk.W)

        self.log_text = tk.Text(right_frame, state='disabled', height=15, font=("Courier New", 10), bg="#f0f0f0")
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)

    # Оновлює вміст віджета Listbox на основі поточного стану списку self.objects_list.
    def update_listbox(self):
        self.listbox.delete(0, tk.END)  # Повне очищення списку перед оновленням.
        for obj in self.objects_list:
            self.listbox.insert(tk.END, obj)

    # Запис дії користувача у протокол з часовою міткою.
    def log_action(self, action):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {action}\n"

        # Тимчасове ввімкнення поля для запису.
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)  # Автоматична прокрутка до останнього запису.
        # Вимкнення поля для запобігання редагуванню користувачем.
        self.log_text.config(state='disabled')

    # Генерує початковий набір об'єктів для ранжування.
    def generate_initial_objects(self):
        # Згідно з завданням, множина повинна містити не менше 12 об'єктів.
        sample_objects = [
            "Яблуко", "Банан", "Апельсин", "Груша", "Ківі", "Манго",
            "Ананас", "Полуниця", "Виноград", "Персик", "Слива", "Абрикос"
        ]

        self.objects_list.clear()
        self.object_original_indices.clear()

        # Заповнення списку об'єктів та збереження їх початкових індексів.
        for i, obj in enumerate(sample_objects):
            self.objects_list.append(obj)
            self.object_original_indices[obj] = i

        self.update_listbox()
        self.log_action("Згенеровано новий набір об'єктів (фрукти).")

    # Завантажує список об'єктів з текстового файлу.
    def load_from_file(self):
        filepath = filedialog.askopenfilename(
            title="Оберіть файл з об'єктами",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if not filepath:
            return  # Користувач скасував вибір файлу.

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_objects = [line.strip() for line in f if line.strip()]

            if len(loaded_objects) < 2:
                messagebox.showwarning("Помилка", "Файл має містити щонайменше 2 об'єкти.")
                return

            self.objects_list.clear()
            self.object_original_indices.clear()

            for i, obj in enumerate(loaded_objects):
                self.objects_list.append(obj)
                self.object_original_indices[obj] = i

            self.update_listbox()
            self.log_action(f"Завантажено {len(loaded_objects)} об'єктів з файлу: {filepath}")
        except Exception as e:
            messagebox.showerror("Помилка читання файлу", f"Не вдалося прочитати файл: {e}")
            self.log_action(f"Помилка при завантаженні файлу: {filepath}")

    # Дозволяє користувачу додати об'єкт вручну через діалогове вікно.
    def add_manually(self):
        new_obj = simpledialog.askstring("Додати об'єкт", "Введіть назву нового об'єкта:")
        if new_obj and new_obj.strip():
            new_obj = new_obj.strip()
            if new_obj in self.objects_list:
                messagebox.showwarning("Помилка", "Такий об'єкт вже існує у списку.")
                return

            # Додавання нового об'єкта та присвоєння йому унікального індексу.
            self.objects_list.append(new_obj)
            new_index = len(self.object_original_indices)
            self.object_original_indices[new_obj] = new_index

            self.update_listbox()
            self.log_action(f"Додано новий об'єкт: '{new_obj}'")
        else:
            self.log_action("Спроба додати порожній об'єкт була скасована.")

    # Переміщує виділений елемент на одну позицію вгору у списку.
    def move_up(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return

        idx = selected_indices[0]
        if idx > 0:
            # Обмін елементів місцями.
            obj = self.objects_list.pop(idx)
            self.objects_list.insert(idx - 1, obj)

            self.update_listbox()
            self.listbox.selection_set(idx - 1)
            self.log_action(f"Об'єкт '{obj}' переміщено вгору.")

    # Переміщує виділений елемент на одну позицію вниз у списку.
    def move_down(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return

        idx = selected_indices[0]
        if idx < len(self.objects_list) - 1:
            obj = self.objects_list.pop(idx)
            self.objects_list.insert(idx + 1, obj)

            self.update_listbox()
            self.listbox.selection_set(idx + 1)
            self.log_action(f"Об'єкт '{obj}' переміщено вниз.")

    # Видаляє виділений об'єкт зі списку ранжування.
    def remove_object(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return

        idx = selected_indices[0]
        obj = self.objects_list[idx]

        if messagebox.askyesno("Підтвердження", f"Ви впевнені, що хочете видалити '{obj}'?"):
            self.objects_list.pop(idx)
            self.update_listbox()
            self.log_action(f"Об'єкт '{obj}' видалено зі списку.")

    # Генерує та зберігає матрицю попарних порівнянь у текстовий файл.
    def save_matrix(self):
        if not self.objects_list:
            messagebox.showwarning("Помилка", "Список об'єктів порожній. Збереження неможливе.")
            return

        # Визначення розміру матриці на основі початкової кількості об'єктів.
        n = len(self.object_original_indices)
        matrix = [[0] * n for _ in range(n)]

        # Створення словника "об'єкт -> поточний ранг (позиція у списку)".
        current_ranks = {obj: rank for rank, obj in enumerate(self.objects_list)}

        # Отримання списку всіх початкових об'єктів, відсортованих за їх індексами.
        all_original_objects = sorted(self.object_original_indices.keys(),
                                      key=lambda k: self.object_original_indices[k])

        # Заповнення матриці на основі фінального ранжування.
        for obj_i in all_original_objects:
            for obj_j in all_original_objects:
                i = self.object_original_indices[obj_i]
                j = self.object_original_indices[obj_j]

                # Пропускаємо порівняння, якщо один з об'єктів був видалений.
                if obj_i not in current_ranks or obj_j not in current_ranks:
                    continue

                if i == j:
                    matrix[i][j] = 0  # Елементи на головній діагоналі дорівнюють 0.
                elif current_ranks[obj_i] < current_ranks[obj_j]:
                    matrix[i][j] = 1  # obj_i має вищий ранг, ніж obj_j.
                    matrix[j][i] = -1  # Відповідно, obj_j має нижчий ранг.

        # Збереження матриці у файл.
        try:
            with open("ranking_matrix.txt", "w", encoding="utf-8") as f:
                f.write("Матриця попарних порівнянь:\n\n")

                # Формування заголовка стовпців з назвами об'єктів.
                header = "\t" + "\t".join(all_original_objects)
                f.write(header + "\n")

                # Запис рядків матриці з назвами об'єктів як заголовками рядків.
                for i, row in enumerate(matrix):
                    row_label = all_original_objects[i]
                    row_str = "\t".join(map(str, row))
                    f.write(f"{row_label}\t{row_str}\n")

            messagebox.showinfo("Успіх!", "Матрицю попарних порівнянь успішно збережено у файл 'ranking_matrix.txt'")
            self.log_action("Результат ранжування збережено у вигляді матриці.")
        except Exception as e:
            messagebox.showerror("Помилка збереження", f"Не вдалося зберегти файл: {e}")
            self.log_action(f"Помилка при збереженні матриці: {e}")


# Точка входу для запуску програми.
if __name__ == "__main__":
    app = RankingApp()
    app.mainloop()