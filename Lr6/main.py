import time


class Rule:
    """
    Клас для представлення однієї продукції (правила)
    <N, A, P, F>
    """

    def __init__(self, name, check_P, check_A, execute_F):
        self.name = name  # N: Ідентифікатор продукції
        self.check_P = check_P  # P: Функція-умова використання (повертає bool)
        self.check_A = check_A  # A: Функція-ядро (повертає bool)
        self.execute_F = execute_F  # F: Функція, що виконується


class InferenceEngine:
    """
    Клас "Вирішувач". Реалізує алгоритм роботи експертної системи
    """

    def __init__(self, rules_base):
        self.rules_base = rules_base  # База правил (продукцій)
        self.log = []

    def log_action(self, message):
        """Додає запис у протокол роботи."""
        self.log.append(message)
        print(message)

    def run(self, working_memory):
        """
        Запускає основний цикл роботи вирішувача.
        """
        self.log = []
        self.log_action(f"--- Запуск вирішувача ---")
        self.log_action(f"Початковий стан фактів: {self.format_facts(working_memory)}")

        iteration = 0
        max_iterations = 20  # Захист від нескінченного циклу

        while iteration < max_iterations:
            iteration += 1
            rule_fired = False
            self.log_action(f"\n===== Ітерація {iteration} =====")

            for i, rule in enumerate(self.rules_base, 1):
                self.log_action(f"-> Перевірка правила {i}: {rule.name}")

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
                        self.log_action(f"   → Оновлений стан: {self.format_facts(working_memory)}")

                        rule_fired = True
                        self.log_action(f"   ⤴ Повернення на початок списку продукцій")
                        break  # Перехід на початок списку продукцій
                else:
                    self.log_action(f"   ✗ Правило пропущено (Блок P не виконується)")

            # Перевірка цільового стану
            if working_memory["f7"]:
                self.log_action("\n" + "="*50)
                self.log_action("🎯 ЦІЛЬОВИЙ СТАН ДОСЯГНУТО!")
                self.log_action("   f7 = True (вода тепла)")
                self.log_action("="*50)
                break

            # Якщо жодне правило не спрацювало за ітерацію
            if not rule_fired:
                self.log_action("\n" + "="*50)
                self.log_action("⚠ Жодне правило не було активовано.")
                self.log_action("   Очікування зміни температури...")
                self.log_action("="*50)
                break

        if iteration == max_iterations:
            self.log_action("\n" + "="*50)
            self.log_action("⚠ Роботу зупинено: перевищено ліміт ітерацій")
            self.log_action("="*50)

        self.log_action(f"\nКінцевий стан фактів: {self.format_facts(working_memory)}")
        return self.log

    def format_facts(self, wm):
        """Форматує факти для зручного відображення"""
        return "\n      ".join([f"{k}={v}" for k, v in wm.items()])


# --- База правил експертної системи керування душем ---

RULES_BASE = [
    Rule(
        name="Продукція 1: Додати холодної води (якщо гаряча)",
        check_P=lambda wm: not wm["f4"] and not wm["f7"],  # ¬f4 ∧ ¬f7
        check_A=lambda wm: wm["f1"] and wm["f5"],  # f1 ∧ f5
        execute_F=lambda wm: (
            f"ВідкритиВентильХолодноїВодиНа({wm['f8']})",
            {"f4": True, "f5": False}  # Вентиль холодної води повністю відкрито, вода перестає бути гарячою
        )
    ),
    Rule(
        name="Продукція 2: Додати гарячої води (якщо холодна)",
        check_P=lambda wm: not wm["f3"] and not wm["f7"],  # ¬f3 ∧ ¬f7
        check_A=lambda wm: wm["f2"] and wm["f6"],  # f2 ∧ f6
        execute_F=lambda wm: (
            f"ВідкритиВентильГарячоїВодиНа({wm['f8']})",
            {"f3": True, "f6": False}  # Вентиль гарячої води повністю відкрито, вода перестає бути холодною
        )
    ),
    Rule(
        name="Продукція 3: Закрити гарячу воду (якщо гаряча і вентиль повністю відкритий)",
        check_P=lambda wm: wm["f3"] and not wm["f7"],  # f3 ∧ ¬f7
        check_A=lambda wm: wm["f1"] and wm["f2"] and wm["f5"],  # f1 ∧ f2 ∧ f5
        execute_F=lambda wm: (
            "ЗакритиВентильГарячоїВоди()",
            {"f1": False, "f3": False, "f5": False, "f7": True}  # Закриваємо гарячу воду, досягаємо теплої
        )
    ),
    Rule(
        name="Продукція 4: Закрити холодну воду (якщо холодна і вентиль повністю відкритий)",
        check_P=lambda wm: wm["f4"] and not wm["f7"],  # f4 ∧ ¬f7
        check_A=lambda wm: wm["f1"] and wm["f2"] and wm["f6"],  # f1 ∧ f2 ∧ f6
        execute_F=lambda wm: (
            "ЗакритиВентильХолодноїВоди()",
            {"f2": False, "f4": False, "f6": False, "f7": True}  # Закриваємо холодну воду, досягаємо теплої
        )
    )
]


def print_header(title):
    """Виводить красивий заголовок"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_facts_legend():
    """Виводить легенду фактів"""
    print("\n📋 ЛЕГЕНДА ФАКТІВ:")
    print("   f1 – вентиль гарячої води відкритий")
    print("   f2 – вентиль холодної води відкритий")
    print("   f3 – вентиль гарячої води повністю відкритий")
    print("   f4 – вентиль холодної води повністю відкритий")
    print("   f5 – вода гаряча")
    print("   f6 – вода холодна")
    print("   f7 – вода тепла (ЦІЛЬОВИЙ СТАН)")
    print("   f8 – крок відкриття вентиля")


# Створюємо вирішувач
engine = InferenceEngine(RULES_BASE)

# --- СЦЕНАРІЙ 1: Початковий стан - холодна вода ---
print_header("СЦЕНАРІЙ 1: Вода холодна (f6=True)")
print_facts_legend()

initial_state_1 = {
    "f1": True,   # Вентиль гарячої води відкритий
    "f2": True,   # Вентиль холодної води відкритий
    "f3": False,  # Вентиль гарячої води НЕ повністю відкритий
    "f4": False,  # Вентиль холодної води НЕ повністю відкритий
    "f5": False,  # Вода НЕ гаряча
    "f6": True,   # Вода холодна
    "f7": False,  # Вода НЕ тепла
    "f8": 1       # Крок відкриття = 1
}

engine.run(initial_state_1)
time.sleep(1)


# --- СЦЕНАРІЙ 2: Початковий стан - гаряча вода ---
print_header("СЦЕНАРІЙ 2: Вода гаряча (f5=True)")
print_facts_legend()

initial_state_2 = {
    "f1": True,   # Вентиль гарячої води відкритий
    "f2": True,   # Вентиль холодної води відкритий
    "f3": False,  # Вентиль гарячої води НЕ повністю відкритий
    "f4": False,  # Вентиль холодної води НЕ повністю відкритий
    "f5": True,   # Вода гаряча
    "f6": False,  # Вода НЕ холодна
    "f7": False,  # Вода НЕ тепла
    "f8": 1       # Крок відкриття = 1
}

engine.run(initial_state_2)