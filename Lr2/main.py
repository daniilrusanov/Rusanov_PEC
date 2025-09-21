import tkinter as tk
from tkinter import messagebox
import json

# КЛАС 1: ВІКНО РАНЖУВАННЯ ДЛЯ ОДНОГО ЕКСПЕРТА
class SingleExpertRanker(tk.Toplevel):
    """
    Це вікно є інструментом для одного експерта.
    Воно отримує ім'я експерта та початковий список об'єктів,
    дозволяє їх ранжувати і зберігає результат у файл.
    """

    def __init__(self, parent, expert_name, initial_objects, original_indices):
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()

        self.expert_name = expert_name
        self.initial_objects = initial_objects
        self.object_original_indices = original_indices
        self.objects_list = list(initial_objects)

        self.title(f"Сесія ранжування для: {self.expert_name}")
        self.geometry("600x500")

        self.create_widgets()
        self.update_listbox()
        parent.log_action(f"Запущено сесію для експерта {self.expert_name}.")

    def create_widgets(self):
        # Створення елементів інтерфейсу: список, кнопки керування
        main_frame = tk.Frame(self, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Відсортуйте об'єкти (вищий ранг - вище у списку):", font=("Arial", 11)).pack(
            anchor=tk.W)
        self.listbox = tk.Listbox(main_frame, selectmode=tk.SINGLE, height=15)
        self.listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        controls_frame = tk.Frame(main_frame)
        controls_frame.pack(fill=tk.X, pady=5)
        tk.Button(controls_frame, text="Вгору", command=self.move_up).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        tk.Button(controls_frame, text="Вниз", command=self.move_down).pack(side=tk.LEFT, expand=True, fill=tk.X,
                                                                            padx=5)
        tk.Button(controls_frame, text="Видалити", command=self.remove_object, bg="#ff8a80").pack(side=tk.LEFT,
                                                                                                  expand=True,
                                                                                                  fill=tk.X, padx=5)

        tk.Button(main_frame, text="Завершити та надіслати результат", command=self.submit_results, bg="#80c8ff",
                  font=("Arial", 11, "bold")).pack(fill=tk.X, pady=10)

    def update_listbox(self):
        # Оновлення візуального списку
        self.listbox.delete(0, tk.END)
        for obj in self.objects_list:
            self.listbox.insert(tk.END, obj)

    def move_up(self):
        # Переміщення елемента вгору
        selected_indices = self.listbox.curselection()
        if not selected_indices: return
        idx = selected_indices[0]
        if idx > 0:
            obj = self.objects_list.pop(idx)
            self.objects_list.insert(idx - 1, obj)
            self.update_listbox()
            self.listbox.selection_set(idx - 1)

    def move_down(self):
        # Переміщення елемента вниз
        selected_indices = self.listbox.curselection()
        if not selected_indices: return
        idx = selected_indices[0]
        if idx < len(self.objects_list) - 1:
            obj = self.objects_list.pop(idx)
            self.objects_list.insert(idx + 1, obj)
            self.update_listbox()
            self.listbox.selection_set(idx + 1)

    def remove_object(self):
        # Видалення елемента зі списку
        selected_indices = self.listbox.curselection()
        if not selected_indices: return
        idx = selected_indices[0]
        self.objects_list.pop(idx)
        self.update_listbox()

    def submit_results(self):
        # Збереження результатів експерта у JSON-файл
        ranked_objects = self.objects_list
        deleted_objects = [obj for obj in self.initial_objects if obj not in ranked_objects]

        result_data = {
            "expert_name": self.expert_name,
            "ranked_objects": ranked_objects,
            "deleted_objects": deleted_objects
        }

        filename = f"{self.expert_name}_results.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Успіх", f"Результати для {self.expert_name} збережено!", parent=self)
            self.master.log_action(f"Експерт {self.expert_name} завершив роботу. Результат у файлі {filename}.")
            self.master.expert_finished(self.expert_name)  # Повідомляємо головне вікно
            self.destroy()
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти файл: {e}", parent=self)


# КЛАС 2: ГОЛОВНЕ ВІКНО-КОНТРОЛЕР ДЛЯ УПРАВЛІННЯ ПРОЦЕСОМ
class CollectiveRankingController(tk.Tk):
    """
    Це головне вікно, що керує всім процесом колективного ранжування.
    Воно визначає кількість експертів, запускає для них сесії
    та проводить фінальний аналіз результатів.
    """

    def __init__(self):
        super().__init__()
        self.title("Контролер колективного ранжування")
        self.geometry("800x600")

        # Початкові дані
        self.initial_objects = [
            "Яблуко", "Банан", "Апельсин", "Груша", "Ківі", "Манго",
            "Ананас", "Полуниця", "Виноград", "Персик", "Слива", "Абрикос"
        ]
        self.object_original_indices = {obj: i for i, obj in enumerate(self.initial_objects)}

        self.experts = []
        self.finished_experts = set()

        self.create_widgets()
        self.log_action("Програму запущено. Готова до налаштування сесії.")

    def create_widgets(self):
        # --- Верхня панель налаштувань ---
        setup_frame = tk.Frame(self, padx=10, pady=10)
        setup_frame.pack(fill=tk.X)

        tk.Label(setup_frame, text="Кількість експертів:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(0, 10))
        self.num_experts_spinbox = tk.Spinbox(setup_frame, from_=2, to=10, width=5)
        self.num_experts_spinbox.pack(side=tk.LEFT, padx=10)

        self.setup_btn = tk.Button(setup_frame, text="Налаштувати експертів", command=self.setup_experts)
        self.setup_btn.pack(side=tk.LEFT, padx=10)

        # --- Середня панель керування сесією ---
        session_frame = tk.Frame(self, padx=10, pady=10)
        session_frame.pack(fill=tk.X)

        self.start_btn = tk.Button(session_frame, text="Розпочати сесію ранжування", state="disabled",
                                   command=self.start_session)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        self.analyze_btn = tk.Button(session_frame, text="Проаналізувати результати", state="disabled",
                                     command=self.analyze_results)
        self.analyze_btn.pack(side=tk.LEFT, padx=10)

        # --- Нижня панель для протоколу дій ---
        log_frame = tk.Frame(self, padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="Протокол дій:", font=("Arial", 12)).pack(anchor=tk.W)
        self.log_text = tk.Text(log_frame, state='disabled', font=("Courier New", 10), bg="#f0f0f0")
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)

    def log_action(self, action):
        # Запис дій у протокол
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f">> {action}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def setup_experts(self):
        # Налаштування імен експертів
        num_experts = int(self.num_experts_spinbox.get())
        self.experts = [f"Expert_{i + 1}" for i in range(num_experts)]
        self.finished_experts.clear()
        self.start_btn.config(state="normal")
        self.analyze_btn.config(state="disabled")
        self.log_action(f"Налаштовано {num_experts} експертів: {', '.join(self.experts)}.")
        messagebox.showinfo("Налаштовано", f"Створено {num_experts} експертів. Тепер можна розпочинати сесію.")

    def start_session(self):
        # Запуск вікон ранжування для кожного експерта
        if not self.experts:
            messagebox.showwarning("Помилка", "Спочатку налаштуйте експертів!")
            return

        for expert_name in self.experts:
            SingleExpertRanker(self, expert_name, self.initial_objects, self.object_original_indices)

        self.start_btn.config(state="disabled")  # Забороняємо запускати сесію повторно
        self.log_action("Сесію ранжування розпочато для всіх експертів.")

    def expert_finished(self, expert_name):
        # Цей метод викликається, коли експерт завершує роботу
        self.finished_experts.add(expert_name)
        self.log_action(
            f"Отримано результат від {expert_name}. Завершено: {len(self.finished_experts)} з {len(self.experts)}.")
        if len(self.finished_experts) == len(self.experts):
            self.analyze_btn.config(state="normal")
            self.log_action("Всі експерти завершили роботу. Можна переходити до аналізу.")
            messagebox.showinfo("Сесія завершена",
                                "Всі експерти надіслали результати. Натисніть 'Проаналізувати результати'.")

    def analyze_results(self):
        # Збір та аналіз результатів, пошук конфліктів
        all_results = []
        for expert_name in self.experts:
            try:
                with open(f"{expert_name}_results.json", 'r', encoding='utf-8') as f:
                    all_results.append(json.load(f))
            except FileNotFoundError:
                messagebox.showerror("Помилка", f"Не знайдено файл результатів для {expert_name}!")
                return

        # Виявлення конфліктів (об'єкт кимось видалений, а кимось - ні)
        conflicts = {}
        for obj in self.initial_objects:
            kept_by = [res["expert_name"] for res in all_results if obj in res["ranked_objects"]]
            deleted_by = [res["expert_name"] for res in all_results if obj in res["deleted_objects"]]
            if kept_by and deleted_by:
                conflicts[obj] = {"kept_by": kept_by, "deleted_by": deleted_by}

        self.log_action(f"Знайдено {len(conflicts)} конфліктних об'єктів.")

        final_object_list = list(self.initial_objects)
        if conflicts:
            # Якщо є конфлікти, запускаємо вікно для їх вирішення
            final_object_list = self.resolve_conflicts(conflicts)

        self.generate_final_report(all_results, final_object_list)

    def resolve_conflicts(self, conflicts):
        # Діалогове вікно для вирішення конфліктів
        dialog = tk.Toplevel(self)
        dialog.title("Вирішення конфліктів")
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog,
                 text="Деякі об'єкти були видалені одними експертами та залишені іншими.\nПрийміть фінальне рішення:",
                 padx=10, pady=10).pack()

        decisions = {}
        for obj, data in conflicts.items():
            frame = tk.Frame(dialog, borderwidth=1, relief="raised", padx=10, pady=10)
            frame.pack(padx=10, pady=5, fill=tk.X)

            label_text = f"Об'єкт: '{obj}'\nЗалишили: {', '.join(data['kept_by'])}\nВидалили: {', '.join(data['deleted_by'])}"
            tk.Label(frame, text=label_text, justify=tk.LEFT).pack(side=tk.LEFT, expand=True)

            decisions[obj] = tk.StringVar(value="keep")
            tk.Radiobutton(frame, text="Залишити", variable=decisions[obj], value="keep").pack(anchor=tk.W)
            tk.Radiobutton(frame, text="Видалити", variable=decisions[obj], value="remove").pack(anchor=tk.W)

        final_objects = list(self.initial_objects)

        def apply_decisions():
            for obj, decision_var in decisions.items():
                if decision_var.get() == "remove":
                    if obj in final_objects:
                        final_objects.remove(obj)
                    self.log_action(f"Конфлікт по '{obj}': прийнято рішення видалити.")
                else:
                    self.log_action(f"Конфлікт по '{obj}': прийнято рішення залишити.")
            dialog.destroy()

        tk.Button(dialog, text="Застосувати рішення", command=apply_decisions, pady=10).pack()
        self.wait_window(dialog)  # Чекаємо, поки вікно вирішення конфліктів не закриється
        return final_objects

    def generate_final_report(self, all_results, final_object_list):
        # Генерація фінальної таблиці з рангами
        self.log_action("Генерація фінального звіту...")

        header = ["Поч. номер", "Назва об'єкта"] + self.experts

        # Створюємо словники рангів для швидкого доступу
        expert_ranks = {}
        for res in all_results:
            ranks = {obj: rank + 1 for rank, obj in enumerate(res["ranked_objects"])}
            expert_ranks[res["expert_name"]] = ranks

        # Формуємо рядки для звіту
        report_data = []
        for obj in self.initial_objects:
            if obj not in final_object_list:
                continue  # Пропускаємо об'єкти, які були видалені остаточно

            row = [self.object_original_indices[obj], obj]
            for expert_name in self.experts:
                rank = expert_ranks[expert_name].get(obj, "видалено")
                row.append(rank)
            report_data.append(row)

        # Запис у файл
        try:
            with open("collective_ranking_results.txt", 'w', encoding='utf-8') as f:
                f.write("Матриця рангів, присвоєних кожним експертом\n\n")
                f.write("\t".join(map(str, header)) + "\n")
                for row in report_data:
                    f.write("\t".join(map(str, row)) + "\n")

            self.log_action("Фінальний звіт 'collective_ranking_results.txt' успішно згенеровано.")
            messagebox.showinfo("Завершено", "Фінальний звіт збережено у файл 'collective_ranking_results.txt'")
        except Exception as e:
            self.log_action(f"Помилка при генерації звіту: {e}")
            messagebox.showerror("Помилка", f"Не вдалося зберегти звіт: {e}")

# ТОЧКА ВХОДУ В ПРОГРАМУ
if __name__ == "__main__":
    app = CollectiveRankingController()
    app.mainloop()