import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import Dict, List, Tuple, Optional


# --- 1. CORE EXPERT SYSTEM LOGIC (MODIFIED FOR GUI) ---

class Rule:
    """
    Клас для представлення однієї продукції (правила)
    <N, A, P, F>
    """

    def __init__(self, name, check_P, check_A, execute_F):
        self.name = name
        self.check_P = check_P
        self.check_A = check_A
        self.execute_F = execute_F


class InferenceEngine:
    """
    Клас "Вирішувач". Реалізує алгоритм роботи експертної системи
    Модифікований для роботи з GUI
    """

    def __init__(self, rules_base):
        self.rules_base = rules_base
        self.log = []
        self.fired_rules_log = []

    def reset(self):
        """Скидає лог роботи"""
        self.log = []
        self.fired_rules_log = []

    def log_action(self, message):
        """Додає запис у протокол роботи."""
        self.log.append(message)

    def simulate_temperature_after_action(self, working_memory):
        """
        Симулює зміну температури води після виконання дії.
        Логіка базується на стані вентилів.
        """
        # Якщо обидва вентилі відкриті (повністю або частково)
        if working_memory["f3"] and working_memory["f4"]:
            # Обидва повністю відкриті -> вода тепла
            working_memory["f5"] = False
            working_memory["f6"] = False
            working_memory["f7"] = True
            return "тепла (обидва вентилі відкриті)"

        elif working_memory["f3"] and not working_memory["f4"]:
            # Тільки гарячий повністю відкритий -> вода гаряча
            working_memory["f5"] = True
            working_memory["f6"] = False
            working_memory["f7"] = False
            return "гаряча (тільки гарячий вентиль)"

        elif not working_memory["f3"] and working_memory["f4"]:
            # Тільки холодний повністю відкритий -> вода холодна
            working_memory["f5"] = False
            working_memory["f6"] = True
            working_memory["f7"] = False
            return "холодна (тільки холодний вентиль)"

        elif working_memory["f1"] and working_memory["f2"]:
            # Обидва частково відкриті -> може бути тепла
            if not working_memory["f5"] and not working_memory["f6"]:
                working_memory["f7"] = True
                return "тепла (збалансовані вентилі)"

        # За замовчуванням залишаємо поточний стан
        if working_memory["f5"]:
            return "гаряча"
        elif working_memory["f6"]:
            return "холодна"
        else:
            return "тепла"

    def run(self, working_memory) -> Tuple[bool, str]:
        """
        Запускає основний цикл роботи вирішувача.
        Повертає (success, log_text)
        """
        self.reset()
        self.log_action("--- Запуск вирішувача ---")
        self.log_action(f"Початковий стан фактів:\n{self.format_facts(working_memory)}\n")

        iteration = 0
        max_iterations = 20

        while iteration < max_iterations:
            iteration += 1
            rule_fired = False
            self.log_action(f"\n{'=' * 50}")
            self.log_action(f"ІТЕРАЦІЯ {iteration}")
            self.log_action(f"{'=' * 50}")

            for i, rule in enumerate(self.rules_base, 1):
                self.log_action(f"\n→ Перевірка правила {i}: {rule.name}")

                # 1. Чи виконується умова блоку P?
                p_result = rule.check_P(working_memory)
                self.log_action(f"   [Блок P] Умова використання: {p_result}")

                if p_result:
                    # 2. Чи виконується умова блоку A?
                    a_result = rule.check_A(working_memory)
                    self.log_action(f"   [Блок A] Ядро продукції: {a_result}")

                    if a_result:
                        # 3. Виконання блоку F
                        action_description, new_state = rule.execute_F(working_memory)
                        self.log_action(f"   [Блок F] ✓ ВИКОНАНО: {action_description}")
                        working_memory.update(new_state)
                        self.log_action(f"   → Оновлений стан:\n{self.format_facts(working_memory)}")

                        # 🌡️ СИМУЛЯЦІЯ ЗМІНИ ТЕМПЕРАТУРИ
                        temp_result = self.simulate_temperature_after_action(working_memory)
                        self.log_action(f"\n   🌡️ Симуляція температури: вода стала {temp_result}")
                        self.log_action(f"   → Стан після зміни температури:\n{self.format_facts(working_memory)}")

                        # Зберігаємо інформацію про спрацьоване правило
                        self.fired_rules_log.append({
                            'rule': rule,
                            'action': action_description,
                            'state': dict(working_memory)
                        })

                        rule_fired = True
                        self.log_action(f"   ⤴ Повернення на початок списку продукцій")
                        break
                else:
                    self.log_action(f"   ✗ Правило пропущено")

            # Перевірка цільового стану
            if working_memory["f7"]:
                self.log_action(f"\n{'=' * 50}")
                self.log_action("🎯 ЦІЛЬОВИЙ СТАН ДОСЯГНУТО!")
                self.log_action("   f7 = True (вода тепла)")
                self.log_action(f"{'=' * 50}")
                return True, self.get_log_text()

            # Якщо жодне правило не спрацювало
            if not rule_fired:
                self.log_action(f"\n{'=' * 50}")
                self.log_action("⚠ Жодне правило не було активовано.")
                self.log_action("   Неможливо досягти цільового стану.")
                self.log_action(f"{'=' * 50}")
                return False, self.get_log_text()

        self.log_action(f"\n{'=' * 50}")
        self.log_action("⚠ Перевищено ліміт ітерацій")
        self.log_action(f"{'=' * 50}")
        return False, self.get_log_text()

    def format_facts(self, wm):
        """Форматує факти для зручного відображення"""
        facts = []
        for k, v in wm.items():
            if k == "f8":
                facts.append(f"   {k} = {v}")
            else:
                facts.append(f"   {k} = {v}")
        return "\n".join(facts)

    def get_log_text(self):
        """Повертає весь лог як текст"""
        return "\n".join(self.log)

    def get_explanation(self) -> str:
        """Повертає пояснення 'ЯК?' досягнуто результат"""
        if not self.fired_rules_log:
            return "Жодне правило не було виконано."

        explanation = ["-" * 50]
        explanation.append("ПОЯСНЕННЯ 'ЯК ДОСЯГНУТО РЕЗУЛЬТАТ?'")
        explanation.append("-" * 50 + "\n")

        for i, entry in enumerate(self.fired_rules_log, 1):
            rule = entry['rule']
            action = entry['action']

            explanation.append(f"КРОК {i}:")
            explanation.append(f"  Правило: {rule.name}")
            explanation.append(f"  Дія: {action}")
            explanation.append("")

        explanation.append("-" * 50)
        explanation.append("Кінець пояснення")
        return "\n".join(explanation)


# --- 2. GUI APPLICATION ---

class ShowerApp:
    """
    GUI додаток для експертної системи керування душем
    """

    def __init__(self, root: tk.Tk, inference_engine: InferenceEngine):
        self.root = root
        self.engine = inference_engine
        self.fact_vars: Dict[str, tk.BooleanVar] = {}

        # --- Setup the UI ---
        self.root.title("ЛР №5: GUI Експертної Системи 'Керування Душем'")
        self.root.geometry("600x700")

        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TCheckbutton", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Result.TLabel", font=("Segoe UI", 11, "bold"), padding=10)
        style.configure("Success.Result.TLabel", foreground="green")
        style.configure("Error.Result.TLabel", foreground="red")

        self.create_widgets()

    def create_widgets(self):
        """Створює всі GUI компоненти"""
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill="both", expand=True)

        # --- 1. Заголовок ---
        title_label = ttk.Label(
            main_frame,
            text="🚿 Система Керування Душем",
            style="Header.TLabel"
        )
        title_label.pack(pady=(0, 15))

        # --- 2. Фрейм з перемикачами (Toggles) ---
        toggles_frame = ttk.LabelFrame(
            main_frame,
            text=" Початковий стан фактів ",
            padding="10"
        )
        toggles_frame.pack(fill="x", expand=False, pady=10)

        # Створюємо перемикачі для кожного факту
        facts_description = {
            'f1': 'f1 - Вентиль гарячої води відкритий',
            'f2': 'f2 - Вентиль холодної води відкритий',
            'f3': 'f3 - Вентиль гарячої води повністю відкритий',
            'f4': 'f4 - Вентиль холодної води повністю відкритий',
            'f5': 'f5 - Вода гаряча',
            'f6': 'f6 - Вода холодна',
            'f7': 'f7 - Вода тепла (ЦІЛЬОВИЙ СТАН)',
        }

        # Значення за замовчуванням
        default_values = {
            'f1': True,
            'f2': True,
            'f3': False,
            'f4': False,
            'f5': False,
            'f6': True,
            'f7': False
        }

        for fact_id, description in facts_description.items():
            var = tk.BooleanVar(value=default_values[fact_id])
            chk = ttk.Checkbutton(
                toggles_frame,
                text=description,
                variable=var,
                style="TCheckbutton"
            )
            chk.pack(anchor="w", padx=5, pady=3)
            self.fact_vars[fact_id] = var

        # --- 3. Кнопки керування ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=15)

        self.run_button = ttk.Button(
            button_frame,
            text="▶ Запустити систему",
            command=self.run_system,
            style="TButton"
        )
        self.run_button.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.how_button = ttk.Button(
            button_frame,
            text="📖 Пояснення 'Як?'",
            command=self.show_explanation,
            state="disabled"
        )
        self.how_button.pack(side="left", expand=True, fill="x", padx=5)

        self.reset_button = ttk.Button(
            button_frame,
            text="🔄 Скинути",
            command=self.reset_system
        )
        self.reset_button.pack(side="left", expand=True, fill="x", padx=(5, 0))

        # --- 4. Результат ---
        self.result_label = ttk.Label(
            main_frame,
            text="Натисніть 'Запустити систему' для початку роботи",
            style="Result.TLabel",
            anchor="center",
            relief="solid",
            borderwidth=1
        )
        self.result_label.pack(fill="x", pady=10)

        # --- 5. Лог виконання (ScrolledText) ---
        log_frame = ttk.LabelFrame(
            main_frame,
            text=" Лог виконання ",
            padding="5"
        )
        log_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.log_text = ScrolledText(
            log_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            height=15,
            state="disabled"
        )
        self.log_text.pack(fill="both", expand=True)

    def run_system(self):
        """
        Обробник кнопки 'Запустити систему'
        """
        # 1. Збираємо початковий стан з перемикачів
        working_memory = {
            'f1': self.fact_vars['f1'].get(),
            'f2': self.fact_vars['f2'].get(),
            'f3': self.fact_vars['f3'].get(),
            'f4': self.fact_vars['f4'].get(),
            'f5': self.fact_vars['f5'].get(),
            'f6': self.fact_vars['f6'].get(),
            'f7': self.fact_vars['f7'].get(),
            'f8': 1  # Крок відкриття
        }

        # 2. Запускаємо систему
        success, log_text = self.engine.run(working_memory)

        # 3. Оновлюємо лог
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, log_text)
        self.log_text.config(state="disabled")
        self.log_text.see(tk.END)  # Прокручуємо до кінця

        # 4. Оновлюємо результат
        if success:
            self.result_label.config(
                text="✅ УСПІХ! Цільовий стан досягнуто (f7 = True)",
                style="Success.Result.TLabel"
            )
            self.how_button.config(state="normal")
        else:
            self.result_label.config(
                text="❌ НЕВДАЧА: Неможливо досягти цільового стану",
                style="Error.Result.TLabel"
            )
            self.how_button.config(state="disabled")

    def show_explanation(self):
        """
        Обробник кнопки 'Пояснення'
        Відкриває нове вікно з поясненням
        """
        explanation_text = self.engine.get_explanation()

        # Створюємо нове вікно
        expl_window = tk.Toplevel(self.root)
        expl_window.title("Пояснення 'Як?'")
        expl_window.geometry("500x400")

        # Створюємо ScrolledText
        text_widget = ScrolledText(
            expl_window,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            padx=10,
            pady=10
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)

        # Вставляємо текст
        text_widget.insert(tk.END, explanation_text)
        text_widget.config(state="disabled")

        # Кнопка закриття
        close_btn = ttk.Button(
            expl_window,
            text="Закрити",
            command=expl_window.destroy
        )
        close_btn.pack(pady=(0, 10))

    def reset_system(self):
        """
        Обробник кнопки 'Скинути'
        Повертає все до початкових значень
        """
        # Скидаємо перемикачі
        default_values = {
            'f1': True,
            'f2': True,
            'f3': False,
            'f4': False,
            'f5': False,
            'f6': True,
            'f7': False
        }

        for fact_id, default_val in default_values.items():
            self.fact_vars[fact_id].set(default_val)

        # Очищаємо лог
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

        # Скидаємо результат
        self.result_label.config(
            text="Натисніть 'Запустити систему' для початку роботи",
            style="Result.TLabel"
        )

        # Вимикаємо кнопку пояснення
        self.how_button.config(state="disabled")


# --- 3. MAIN EXECUTION BLOCK ---

if __name__ == "__main__":
    # --- База правил ---
    RULES_BASE = [
        Rule(
            name="Продукція 1: Додати холодної води (якщо гаряча)",
            check_P=lambda wm: not wm["f4"] and not wm["f7"],
            check_A=lambda wm: wm["f1"] and wm["f5"],
            execute_F=lambda wm: (
                f"ВідкритиВентильХолодноїВодиНа({wm['f8']})",
                {"f4": True}
            )
        ),
        Rule(
            name="Продукція 2: Додати гарячої води (якщо холодна)",
            check_P=lambda wm: not wm["f3"] and not wm["f7"],
            check_A=lambda wm: wm["f2"] and wm["f6"],
            execute_F=lambda wm: (
                f"ВідкритиВентильГарячоїВодиНа({wm['f8']})",
                {"f3": True}
            )
        ),
        Rule(
            name="Продукція 3: Закрити гарячу воду",
            check_P=lambda wm: wm["f3"] and not wm["f7"],
            check_A=lambda wm: wm["f1"] and wm["f2"] and wm["f5"],
            execute_F=lambda wm: (
                "ЗакритиВентильГарячоїВоди()",
                {"f1": False, "f3": False}
            )
        ),
        Rule(
            name="Продукція 4: Закрити холодну воду",
            check_P=lambda wm: wm["f4"] and not wm["f7"],
            check_A=lambda wm: wm["f1"] and wm["f2"] and wm["f6"],
            execute_F=lambda wm: (
                "ЗакритиВентильХолодноїВоди()",
                {"f2": False, "f4": False}
            )
        )
    ]

    # --- Ініціалізація системи ---
    engine = InferenceEngine(RULES_BASE)

    # --- Створення GUI ---
    root_window = tk.Tk()
    app = ShowerApp(root_window, engine)

    # --- Запуск додатку ---
    root_window.mainloop()