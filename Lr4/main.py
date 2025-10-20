# coding: utf-8
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import json
import itertools
import time

class SingleExpertRanker(tk.Toplevel):
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
        self.listbox.delete(0, tk.END)
        for obj in self.objects_list:
            self.listbox.insert(tk.END, obj)

    def move_up(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices: return
        idx = selected_indices[0]
        if idx > 0:
            obj = self.objects_list.pop(idx)
            self.objects_list.insert(idx - 1, obj)
            self.update_listbox()
            self.listbox.selection_set(idx - 1)

    def move_down(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices: return
        idx = selected_indices[0]
        if idx < len(self.objects_list) - 1:
            obj = self.objects_list.pop(idx)
            self.objects_list.insert(idx + 1, obj)
            self.update_listbox()
            self.listbox.selection_set(idx + 1)

    def remove_object(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices: return
        idx = selected_indices[0]
        self.objects_list.pop(idx)
        self.update_listbox()

    def submit_results(self):
        ranked_objects = self.objects_list
        deleted_objects = [obj for obj in self.initial_objects if obj not in ranked_objects]
        result_data = {"expert_name": self.expert_name, "ranked_objects": ranked_objects,
                       "deleted_objects": deleted_objects}
        filename = f"{self.expert_name}_results.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Успіх", f"Результати для {self.expert_name} збережено!", parent=self)
            self.master.log_action(f"Експерт {self.expert_name} завершив роботу. Результат у файлі {filename}.")
            self.master.expert_finished(self.expert_name)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти файл: {e}", parent=self)

class ResultsViewer(tk.Toplevel):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.title("Індивідуальні ранжування експертів")
        self.geometry("800x400")
        self.data = data
        self.create_widgets()

    def create_widgets(self):
        frame = tk.Frame(self, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        columns = self.data['headers']
        self.tree = ttk.Treeview(frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='center')
        for row in self.data['rows']:
            self.tree.insert('', tk.END, values=row)
        self.tree.pack(fill=tk.BOTH, expand=True)
        tk.Button(frame, text="Зберегти для друку", command=self.save_for_print, pady=5).pack(pady=10)

    def save_for_print(self):
        filename = "rankings_summary.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Індивідуальні ранжування експертів\n\n")
                headers = self.data['headers']
                f.write("\t".join(headers) + "\n")
                f.write("-" * 8 * len(headers) + "\n")
                for row in self.data['rows']:
                    f.write("\t".join(map(str, row)) + "\n")
            messagebox.showinfo("Успіх", f"Дані для друку збережено у файл '{filename}'", parent=self)
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося зберегти файл: {e}", parent=self)

class CollectiveRankingController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Система підтримки прийняття рішень (ЛР 2-4)")
        self.geometry("800x700")

        # Базові налаштування
        self.initial_objects_base = ["Яблуко", "Банан", "Апельсин", "Груша", "Ківі", "Манго",
                                     "Ананас", "Полуниця", "Виноград", "Персик", "Слива", "Абрикос"]
        self.experts_list = []
        self.finished_experts = set()

        # Сховища результатів
        self.lab2_results = None  # Зберігає дані з collective_ranking_results.txt
        self.expert_rankings_map = None  # Зберігає {Expert: {Obj: Rank}}
        self.best_results = None  # Зберігає 4 компромісні ранжування з ЛР№3
        self.initial_weights = []  # Зберігає початкові ваги, використані в ЛР№3

        self.create_widgets()
        self.log_action("Програму запущено.")

    def create_widgets(self):
        # --- Крок 1: Проведення експертизи (ЛР№2) ---
        lab2_frame = tk.LabelFrame(self, text="Крок 1: Проведення експертизи (ЛР№2)", padx=10, pady=10)
        lab2_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(lab2_frame, text="Кількість експертів:").pack(side=tk.LEFT)
        self.num_experts_spinbox = tk.Spinbox(lab2_frame, from_=2, to=10, width=5)
        self.num_experts_spinbox.pack(side=tk.LEFT, padx=5)
        self.setup_btn = tk.Button(lab2_frame, text="Налаштувати", command=self.setup_experts)
        self.setup_btn.pack(side=tk.LEFT, padx=5)
        self.start_btn = tk.Button(lab2_frame, text="Розпочати сесію", state="disabled", command=self.start_session)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.analyze_btn = tk.Button(lab2_frame, text="Аналіз результатів", state="disabled",
                                     command=self.analyze_lab2_results)
        self.analyze_btn.pack(side=tk.LEFT, padx=5)

        # --- Крок 2: Пошук компромісу (ЛР№3) ---
        lab3_frame = tk.LabelFrame(self, text="Крок 2: Пошук компромісу (ЛР№3)", padx=10, pady=10)
        lab3_frame.pack(fill=tk.X, padx=10, pady=5)
        self.load_btn = tk.Button(lab3_frame, text="Завантажити готовий звіт (ЛР№2)",
                                  command=self.load_lab2_results_from_file)
        self.load_btn.pack(side=tk.LEFT, padx=5)
        self.calc_btn = tk.Button(lab3_frame, text="Розрахувати компромісні ранжування", state="disabled",
                                  command=self.calculate_compromise_rankings)
        self.calc_btn.pack(side=tk.LEFT, padx=5)

        # --- Крок 3: Оцінка компетентності (ЛР№4) ---
        lab4_frame = tk.LabelFrame(self, text="Крок 3: Оцінка компетентності (ЛР№4)", padx=10, pady=10)
        lab4_frame.pack(fill=tk.X, padx=10, pady=5)
        self.calc_comp_btn = tk.Button(lab4_frame, text="Розрахувати компетентність експертів", state="disabled",
                                       command=self.calculate_competency)
        self.calc_comp_btn.pack(side=tk.LEFT, padx=5)

        # --- Протокол дій ---
        log_frame = tk.Frame(self, padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(log_frame, text="Протокол дій:", font=("Arial", 12)).pack(anchor=tk.W)
        self.log_text = tk.Text(log_frame, state='disabled', font=("Courier New", 10), bg="#f0f0f0")
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)

    def log_action(self, action):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f">> {action}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.update_idletasks()

    # --- Методи Кроку 1 (ЛР№2) ---
    def setup_experts(self):
        num_experts = int(self.num_experts_spinbox.get())
        self.experts_list = [f"Expert_{i + 1}" for i in range(num_experts)]
        self.initial_objects = self.initial_objects_base
        self.object_original_indices = {obj: i for i, obj in enumerate(self.initial_objects)}
        self.finished_experts.clear()

        # Скидання стану для нового запуску
        self.start_btn.config(state="normal")
        self.analyze_btn.config(state="disabled")
        self.calc_btn.config(state="disabled")
        self.calc_comp_btn.config(state="disabled")
        self.lab2_results = None
        self.best_results = None
        self.expert_rankings_map = None

        self.log_action(f"Налаштовано {num_experts} експертів: {', '.join(self.experts_list)}.")
        messagebox.showinfo("Налаштовано", f"Створено {num_experts} експертів.")

    def start_session(self):
        for expert_name in self.experts_list:
            SingleExpertRanker(self, expert_name, self.initial_objects, self.object_original_indices)
        self.start_btn.config(state="disabled")
        self.log_action("Сесію ранжування розпочато.")

    def expert_finished(self, expert_name):
        self.finished_experts.add(expert_name)
        self.log_action(
            f"Отримано результат від {expert_name}. Завершено: {len(self.finished_experts)}/{len(self.experts_list)}.")
        if len(self.finished_experts) == len(self.experts_list):
            self.analyze_btn.config(state="normal")
            self.log_action("Всі експерти завершили роботу.")
            messagebox.showinfo("Сесія завершена", "Тепер натисніть 'Аналіз результатів' для обробки даних.")

    def analyze_lab2_results(self):
        self.log_action("Розпочато аналіз результатів експертів (ЛР№2)...")
        all_results = []
        for expert_name in self.experts_list:
            try:
                with open(f"{expert_name}_results.json", 'r', encoding='utf-8') as f:
                    all_results.append(json.load(f))
            except FileNotFoundError:
                messagebox.showerror("Помилка", f"Не знайдено файл результатів для {expert_name}!")
                return

        conflicts = {}
        for obj in self.initial_objects:
            kept_by = [res["expert_name"] for res in all_results if obj in res["ranked_objects"]]
            deleted_by = [res["expert_name"] for res in all_results if obj in res["deleted_objects"]]
            if kept_by and deleted_by:
                conflicts[obj] = {"kept_by": kept_by, "deleted_by": deleted_by}

        self.log_action(f"Знайдено {len(conflicts)} конфліктних об'єктів.")

        final_object_list = list(self.initial_objects)
        if conflicts:
            final_object_list = self.resolve_conflicts(conflicts)

        self.generate_lab2_report(all_results, final_object_list)

    def resolve_conflicts(self, conflicts):
        dialog = tk.Toplevel(self)
        dialog.title("Вирішення конфліктів")
        dialog.transient(self);
        dialog.grab_set()
        tk.Label(dialog, text="Прийміть фінальне рішення по конфліктних об'єктах:", padx=10, pady=10).pack()
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
                if decision_var.get() == "remove" and obj in final_objects:
                    final_objects.remove(obj)
                    self.log_action(f"Конфлікт по '{obj}': прийнято рішення видалити.")
            dialog.destroy()

        tk.Button(dialog, text="Застосувати рішення", command=apply_decisions, pady=10).pack()
        self.wait_window(dialog)
        return final_objects

    def generate_lab2_report(self, all_results, final_object_list):
        self.log_action("Генерація звіту ЛР№2 (collective_ranking_results.txt)...")
        header = ["Поч. номер", "Назва об'єкта"] + self.experts_list
        expert_ranks = {res["expert_name"]: {obj: rank + 1 for rank, obj in enumerate(res["ranked_objects"])} for res in
                        all_results}

        report_data_rows = []
        for obj in self.initial_objects:
            if obj not in final_object_list: continue
            row = [self.object_original_indices[obj], obj]
            for expert_name in self.experts_list:
                rank = expert_ranks[expert_name].get(obj, "видалено")
                row.append(rank)
            report_data_rows.append(row)

        try:
            with open("collective_ranking_results.txt", 'w', encoding='utf-8') as f:
                f.write("Матриця рангів, присвоєних кожним експертом\n\n")
                f.write("\t".join(map(str, header)) + "\n")
                for row in report_data_rows:
                    f.write("\t".join(map(str, row)) + "\n")

            self.log_action("Звіт ЛР№2 успішно згенеровано.")
            messagebox.showinfo("Завершено",
                                "Звіт 'collective_ranking_results.txt' збережено. Дані готові для Кроку 2.")
            self.prepare_data_for_lab3({'headers': header, 'rows': report_data_rows})
        except Exception as e:
            self.log_action(f"Помилка при генерації звіту ЛР№2: {e}")
            messagebox.showerror("Помилка", f"Не вдалося зберегти звіт ЛР№2: {e}")

    # --- Методи Кроку 2 (ЛР№3) ---
    def load_lab2_results_from_file(self):
        filepath = filedialog.askopenfilename(title="Оберіть файл collective_ranking_results.txt",
                                              filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            headers = lines[2].split('\t')
            rows = [line.split('\t') for line in lines[3:]]

            # Скидаємо кнопки ЛР4
            self.calc_comp_btn.config(state="disabled")
            self.best_results = None

            self.prepare_data_for_lab3({'headers': headers, 'rows': rows})
            self.log_action(f"Успішно завантажено дані з файлу: {filepath}")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося прочитати або розпізнати файл: {e}")
            self.log_action(f"Помилка завантаження файлу: {e}")

    def prepare_data_for_lab3(self, data):
        """Готує дані до аналізу та активує кнопку розрахунку."""
        self.lab2_results = data
        self.experts_list = self.lab2_results['headers'][2:]
        self.expert_rankings_map = {
            name: {row[1]: (int(row[i + 2]) if row[i + 2].isdigit() else -1) for row in self.lab2_results['rows']}
            for i, name in enumerate(self.experts_list)
        }

        ResultsViewer(self, self.lab2_results)  # Візуалізація
        self.calc_btn.config(state="normal")
        self.log_action("Дані готові для розрахунку компромісних ранжувань (Крок 2).")

    def calculate_compromise_rankings(self):
        if not self.expert_rankings_map:
            messagebox.showwarning("Увага", "Немає даних для розрахунку. Завершіть Крок 1 або завантажте файл.")
            return

        # --- МОДИФІКАЦІЯ ДЛЯ ЛР№4 (Task 3) ---
        # Запит початкових коефіцієнтів компетентності
        num_experts = len(self.expert_rankings_map)
        default_weights = ",".join(["1"] * num_experts)
        weights_str = simpledialog.askstring("Початкова компетентність (ЛР№4 Task 3)",
                                             f"Введіть початкові коефіцієнти для {num_experts} експертів (через кому):",
                                             initialvalue=default_weights)
        if not weights_str:
            self.log_action("Розрахунок скасовано (не введено коефіцієнти).")
            return
        try:
            self.initial_weights = [float(w.strip()) for w in weights_str.split(',')]
            if len(self.initial_weights) != num_experts: raise ValueError("Невірна кількість коефіцієнтів")
            if sum(self.initial_weights) <= 0: raise ValueError("Сума коефіцієнтів має бути > 0")
        except Exception as e:
            messagebox.showerror("Помилка", f"Некоректні коефіцієнти: {e}")
            return

        self.log_action(f"Розрахунок ЛР№3 буде проведено з початковими коефіцієнтами: {self.initial_weights}")
        # --- Кінець МОДИФІКАЦІЇ ---

        objects = [row[1] for row in self.lab2_results['rows']]
        num_objects = len(objects)

        if num_objects > 8:
            if not messagebox.askyesno("Увага!",
                                       f"Кількість об'єктів ({num_objects}) велика. Розрахунок ({num_objects}!) може зайняти ДУЖЕ багато часу.\n\nПродовжити?"):
                self.log_action("Розрахунок скасовано користувачем.")
                return

        self.log_action("Розпочато розрахунок компромісних ранжувань (ЛР№3)...")
        start_time = time.time()

        best_results = {"cook_seiford": {"rank": None, "score": float('inf')},
                        "gv_median_rank": {"rank": None, "score": float('inf')},
                        "kemeny_snell": {"rank": None, "score": float('inf')},
                        "gv_median_hamming": {"rank": None, "score": float('inf')}}

        for p in itertools.permutations(objects):
            current_ranking = {obj: rank + 1 for rank, obj in enumerate(p)}
            dist_ranks_sum, dist_ranks_max, dist_hamming_sum, dist_hamming_max = 0, 0, 0, 0

            for i, expert_rank_map in enumerate(self.expert_rankings_map.values()):
                weight = self.initial_weights[i]  # Використання ваги

                d_rank = self.calculate_rank_distance(current_ranking, expert_rank_map)
                dist_ranks_sum += d_rank * weight  # Зважена сума
                dist_ranks_max = max(dist_ranks_max, d_rank * weight)  # Зважений максимум

                d_hamming = self.calculate_hamming_distance(current_ranking, expert_rank_map)
                dist_hamming_sum += d_hamming * weight  # Зважена сума
                dist_hamming_max = max(dist_hamming_max, d_hamming * weight)  # Зважений максимум

            if dist_ranks_sum < best_results["cook_seiford"]["score"]: best_results["cook_seiford"] = {"rank": p,
                                                                                                       "score": dist_ranks_sum}
            if dist_ranks_max < best_results["gv_median_rank"]["score"]: best_results["gv_median_rank"] = {"rank": p,
                                                                                                           "score": dist_ranks_max}
            if dist_hamming_sum < best_results["kemeny_snell"]["score"]: best_results["kemeny_snell"] = {"rank": p,
                                                                                                         "score": dist_hamming_sum}
            if dist_hamming_max < best_results["gv_median_hamming"]["score"]: best_results["gv_median_hamming"] = {
                "rank": p, "score": dist_hamming_max}

        end_time = time.time()
        self.log_action(f"Розрахунок ЛР№3 завершено за {end_time - start_time:.2f} секунд.")

        self.best_results = best_results  # Зберігаємо для ЛР№4
        self.generate_compromise_report(best_results)
        self.calc_comp_btn.config(state="normal")  # Активуємо кнопку ЛР№4

    def generate_compromise_report(self, results):
        filename = "compromise_rankings_report.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Звіт про компромісні ранжування (ЛР№3)\n" + "=" * 40 + "\n\n")
                f.write(f"Розрахунок проведено з початковими коефіцієнтами: {self.initial_weights}\n\n")

                f.write("1. Вхідні ранжування експертів:\n")
                headers = self.lab2_results['headers']
                f.write("\t".join(headers) + "\n")
                for row in self.lab2_results['rows']: f.write("\t".join(map(str, row)) + "\n")
                f.write("\n" + "=" * 40 + "\n\n2. Компромісні ранжування:\n\n")

                report_map = {
                    "А) Медіана Кука-Сейфорда (зваж. адитивний, неспівпадання рангів)": "cook_seiford",
                    "Б) ГВ-медіана (зваж. мінімаксний, неспівпадання рангів)": "gv_median_rank",
                    "В) Медіана Кемені-Снела (зваж. адитивний, метрика Хемінга)": "kemeny_snell",
                    "Г) ВГ-медіана (зваж. мінімаксний, метрика Хемінга)": "gv_median_hamming"
                }
                for title, key in report_map.items():
                    f.write(title + ":\n")
                    for i, obj in enumerate(results[key]["rank"]): f.write(f"\t{i + 1}. {obj}\n")
                    f.write(f"\tЗначення критерію (зважене): {results[key]['score']}\n\n")

            self.log_action(f"Звіт ЛР№3 '{filename}' успішно згенеровано.")
            messagebox.showinfo("Завершено", f"Звіт ЛР№3 збережено у файл '{filename}'")
        except Exception as e:
            self.log_action(f"Помилка при генерації звіту ЛР№3: {e}")
            messagebox.showerror("Помилка", f"Не вдалося зберегти звіт ЛР№3: {e}")

    # --- Нові методи Кроку 3 (ЛР№4) ---
    def calculate_competency(self):
        self.log_action("Розпочато розрахунок компетентності (ЛР№4)...")
        if not self.expert_rankings_map or not self.best_results:
            messagebox.showerror("Помилка", "Немає даних для розрахунку. Спочатку виконайте Крок 1 та Крок 2.")
            return

        # Ініціалізація таблиць для звіту
        distances_table = {name: [] for name in self.expert_rankings_map}
        competency_table = {name: [] for name in self.expert_rankings_map}

        # Ітерація по 4 компромісних ранжуваннях, знайдених у ЛР№3
        for key, compromise_data in self.best_results.items():
            compromise_rank_tuple = compromise_data['rank']
            compromise_rank_map = {obj: rank + 1 for rank, obj in enumerate(compromise_rank_tuple)}

            is_hamming = "hamming" in key or "kemeny" in key
            distances_for_this_K = []

            # 1. Розрахунок відстаней (Task 1)
            for expert_name, expert_rank_map in self.expert_rankings_map.items():
                if is_hamming:
                    d = self.calculate_hamming_distance(expert_rank_map, compromise_rank_map)
                else:
                    d = self.calculate_rank_distance(expert_rank_map, compromise_rank_map)

                distances_table[expert_name].append(d)
                distances_for_this_K.append(d)

            # 2. Розрахунок коефіцієнтів компетентності (Task 2)
            # Використовуємо 1 / (d + 1) для уникнення ділення на нуль та забезпечення
            # оберненої пропорційності
            raw_comps = [1.0 / (d + 1.0) for d in distances_for_this_K]
            total_raw_comp = sum(raw_comps)

            if total_raw_comp == 0:
                # Всі відстані нескінченні (малоймовірно) або експертів немає
                normalized_comps = [0.0] * len(raw_comps)
            else:
                # Нормалізація, щоб сума дорівнювала 1 [cite: 220]
                normalized_comps = [rc / total_raw_comp for rc in raw_comps]

            # Запис нормованих коефіцієнтів
            for i, expert_name in enumerate(self.expert_rankings_map.keys()):
                competency_table[expert_name].append(round(normalized_comps[i], 4))

        # 3. Генерація звіту
        self.generate_competency_report(distances_table, competency_table)

    def generate_competency_report(self, distances_table, competency_table):
        filename = "competency_report_lr4.txt"
        headers = ["Експерт", "K1_r (Кук)", "K2_r (ГВ-ранг)", "K1_h (Кемені)", "K2_h (ВГ-Хем)"]

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Звіт про компетентність експертів (ЛР№4)\n")
                f.write(f"На основі компромісних ранжувань, розрахованих з вагами: {self.initial_weights}\n")
                f.write("=" * 80 + "\n\n")

                # Запис Таблиці 1
                f.write("Таблиця 1: Відстані від індивідуальних до компромісних ранжувань\n")
                f.write("\t".join(headers) + "\n")
                for expert_name, distances in distances_table.items():
                    f.write(f"{expert_name}\t" + "\t".join(map(str, distances)) + "\n")

                f.write("\n" + "=" * 80 + "\n\n")

                # Запис Таблиці 2
                f.write("Таблиця 2: Нормалізовані коефіцієнти компетентності (сума=1)\n")
                f.write("\t".join(headers) + "\n")
                for expert_name, competencies in competency_table.items():
                    f.write(f"{expert_name}\t" + "\t".join(map(str, competencies)) + "\n")

            self.log_action(f"Звіт ЛР№4 '{filename}' успішно згенеровано.")
            messagebox.showinfo("Завершено", f"Звіт ЛР№4 збережено у файл '{filename}'")
        except Exception as e:
            self.log_action(f"Помилка при генерації звіту ЛР№4: {e}")
            messagebox.showerror("Помилка", f"Не вдалося зберегти звіт ЛР№4: {e}")

    # --- Допоміжні функції розрахунку відстаней ---
    def calculate_rank_distance(self, r1, r2):
        distance = 0
        for obj, rank1 in r1.items():
            if obj not in r2: continue  # Об'єкт був видалений одним з експертів
            rank2 = r2.get(obj, -1)
            if rank2 != -1 and rank1 != -1:
                distance += abs(rank1 - rank2)
        return distance

    def calculate_hamming_distance(self, r1, r2):
        objects = sorted(list(r1.keys()))
        v1 = self.ranking_to_pairwise_vector(r1, objects)
        v2 = self.ranking_to_pairwise_vector(r2, objects)
        distance = sum(abs(i1 - i2) for i1, i2 in zip(v1, v2) if i1 is not None and i2 is not None)
        return distance

    def ranking_to_pairwise_vector(self, ranking, objects):
        vector = []
        for i in range(len(objects)):
            for j in range(i + 1, len(objects)):
                r1, r2 = ranking.get(objects[i], -1), ranking.get(objects[j], -1)
                if r1 == -1 or r2 == -1:
                    vector.append(None)
                else:
                    vector.append(1 if r1 < r2 else -1)
        return vector

if __name__ == "__main__":
    app = CollectiveRankingController()
    app.mainloop()