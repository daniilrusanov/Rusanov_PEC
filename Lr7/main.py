import sys


class Logger:
    """
    Перенаправляє вивід одночасно в консоль та файл логу.
    """

    def __init__(self, filename: str):
        self.terminal = sys.stdout
        self.logfile = None
        try:
            self.logfile = open(filename, "w", encoding="utf-8")
        except IOError as e:
            print(f"ПОМИЛКА: Не вдалося відкрити файл логу {filename}: {e}")

    def write(self, message: str):
        """Записує повідомлення в термінал та файл."""
        self.terminal.write(message)
        if self.logfile:
            self.logfile.write(message)

    def flush(self):
        """Очищує обидва потоки виводу."""
        self.terminal.flush()
        if self.logfile:
            self.logfile.flush()

    def __enter__(self):
        """Починає перенаправлення stdout."""
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Припиняє перенаправлення stdout та закриває файл логу."""
        sys.stdout = self.terminal
        if self.logfile:
            self.logfile.close()


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
        self.goal_stack = []  # Стек для пояснень "ЧОМУ?"

    def log_action(self, message):
        """Додає запис у протокол роботи."""
        self.log.append(message)
        print(message)

    def explain_why(self):
        """Пояснює ЧОМУ система виконує певну дію."""
        print("\n" + "-" * 10 + " [ПОЯСНЕННЯ 'ЧОМУ?'] " + "-" * 10)
        if not self.goal_stack:
            print("> Це початкова перевірка системи.")
            print("-" * 44 + "\n")
            return

        print("> Я виконую це правило, щоб досягти цільового стану:")
        for i, entry in enumerate(reversed(self.goal_stack)):
            indent = "  " * i
            print(f"{indent}🎯 Правило: {entry['rule_name']}")
            print(f"{indent}📋 Мета: {entry['goal']}")
        print("-" * 44 + "\n")

    def simulate_temperature_change(self, working_memory):
        """
        Симулює зміну температури води після виконання дії.
        Запитує користувача, яка температура стала після дії.
        """
        print("\n" + "~" * 50)
        print("🌡️  ЗМІНА ТЕМПЕРАТУРИ ВОДИ")
        print("~" * 50)

        while True:
            response = input("Яка тепер температура води? (гаряча/холодна/тепла): ").strip().lower()

            if response in ['гаряча', 'hot', 'г']:
                working_memory.update({
                    "f5": True,  # Вода гаряча
                    "f6": False,  # Вода НЕ холодна
                    "f7": False  # Вода НЕ тепла
                })
                print("✓ Встановлено: вода ГАРЯЧА")
                break
            elif response in ['холодна', 'cold', 'х']:
                working_memory.update({
                    "f5": False,  # Вода НЕ гаряча
                    "f6": True,  # Вода холодна
                    "f7": False  # Вода НЕ тепла
                })
                print("✓ Встановлено: вода ХОЛОДНА")
                break
            elif response in ['тепла', 'warm', 'т']:
                working_memory.update({
                    "f5": False,  # Вода НЕ гаряча
                    "f6": False,  # Вода НЕ холодна
                    "f7": True  # Вода тепла
                })
                print("✓ Встановлено: вода ТЕПЛА")
                break
            else:
                print("Будь ласка, введіть: 'гаряча', 'холодна' або 'тепла'")

        print("~" * 50 + "\n")

    def run(self, working_memory):
        """
        Запускає основний цикл роботи вирішувача.
        """
        self.log = []
        self.log_action(f"--- Запуск вирішувача ---")
        self.log_action(f"Початковий стан фактів:\n      {self.format_facts(working_memory)}")

        iteration = 0
        max_iterations = 20  # Захист від нескінченного циклу

        while iteration < max_iterations:
            iteration += 1
            rule_fired = False
            self.log_action(f"\n===== Ітерація {iteration} =====")

            for i, rule in enumerate(self.rules_base, 1):
                self.log_action(f"-> Перевірка правила {i}: {rule.name}")

                # Додаємо правило в стек для пояснень
                self.goal_stack.append({
                    'rule_name': rule.name,
                    'goal': 'Досягти теплої води (f7=True)'
                })

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
                        self.log_action(f"   → Оновлений стан:\n      {self.format_facts(working_memory)}")

                        # ⭐ ЗАПИТУЄМО КОРИСТУВАЧА ПРО НОВУ ТЕМПЕРАТУРУ
                        self.simulate_temperature_change(working_memory)
                        self.log_action(
                            f"   → Стан після зміни температури:\n      {self.format_facts(working_memory)}")

                        rule_fired = True
                        self.goal_stack.pop()
                        self.log_action(f"   ⤴ Повернення на початок списку продукцій")
                        break  # Перехід на початок списку продукцій
                else:
                    self.log_action(f"   ✗ Правило пропущено (Блок P не виконується)")

                # Видаляємо правило зі стеку
                self.goal_stack.pop()

            # Перевірка цільового стану
            if working_memory["f7"]:
                self.log_action("\n" + "=" * 50)
                self.log_action("🎯 ЦІЛЬОВИЙ СТАН ДОСЯГНУТО!")
                self.log_action("   f7 = True (вода тепла)")
                self.log_action("=" * 50)
                break

            # Якщо жодне правило не спрацювало за ітерацію
            if not rule_fired:
                self.log_action("\n" + "=" * 50)
                self.log_action("⚠ Жодне правило не було активовано.")
                self.log_action("   Система не може досягти цільового стану з поточними фактами.")
                self.log_action("=" * 50)
                break

        if iteration == max_iterations:
            self.log_action("\n" + "=" * 50)
            self.log_action("⚠ Роботу зупинено: перевищено ліміт ітерацій")
            self.log_action("=" * 50)

        self.log_action(f"\nКінцевий стан фактів:\n      {self.format_facts(working_memory)}")
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
            {"f4": True}  # Вентиль холодної води повністю відкрито
        )
    ),
    Rule(
        name="Продукція 2: Додати гарячої води (якщо холодна)",
        check_P=lambda wm: not wm["f3"] and not wm["f7"],  # ¬f3 ∧ ¬f7
        check_A=lambda wm: wm["f2"] and wm["f6"],  # f2 ∧ f6
        execute_F=lambda wm: (
            f"ВідкритиВентильГарячоїВодиНа({wm['f8']})",
            {"f3": True}  # Вентиль гарячої води повністю відкрито
        )
    ),
    Rule(
        name="Продукція 3: Закрити гарячу воду (якщо гаряча і вентиль повністю відкритий)",
        check_P=lambda wm: wm["f3"] and not wm["f7"],  # f3 ∧ ¬f7
        check_A=lambda wm: wm["f1"] and wm["f2"] and wm["f5"],  # f1 ∧ f2 ∧ f5
        execute_F=lambda wm: (
            "ЗакритиВентильГарячоїВоди()",
            {"f1": False, "f3": False}  # Закриваємо гарячу воду
        )
    ),
    Rule(
        name="Продукція 4: Закрити холодну воду (якщо холодна і вентиль повністю відкритий)",
        check_P=lambda wm: wm["f4"] and not wm["f7"],  # f4 ∧ ¬f7
        check_A=lambda wm: wm["f1"] and wm["f2"] and wm["f6"],  # f1 ∧ f2 ∧ f6
        execute_F=lambda wm: (
            "ЗакритиВентильХолодноїВоди()",
            {"f2": False, "f4": False}  # Закриваємо холодну воду
        )
    )
]


def print_header(title):
    """Виводить красивий заголовок"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


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


def get_initial_state_from_user():
    """
    Запитує користувача про початковий стан системи.
    """
    print("\n" + "=" * 60)
    print("  НАЛАШТУВАННЯ ПОЧАТКОВОГО СТАНУ")
    print("=" * 60)

    print("\n📋 Введіть початкові значення фактів:")
    print("   (Натисніть Enter для значення за замовчуванням)")

    def ask_fact(description, default):
        default_text = "True" if default else "False"
        while True:
            response = input(f"{description} [{default_text}]: ").strip().lower()
            if response == '':
                return default
            elif response in ['true', 't', 'так', '1', 'yes', 'y']:
                return True
            elif response in ['false', 'f', 'ні', '0', 'no', 'n']:
                return False
            else:
                print("   Будь ласка, введіть: true/false (або натисніть Enter)")

    state = {
        "f1": ask_fact("f1 - Вентиль гарячої води відкритий", True),
        "f2": ask_fact("f2 - Вентиль холодної води відкритий", True),
        "f3": ask_fact("f3 - Вентиль гарячої води повністю відкритий", False),
        "f4": ask_fact("f4 - Вентиль холодної води повністю відкритий", False),
        "f5": ask_fact("f5 - Вода гаряча", False),
        "f6": ask_fact("f6 - Вода холодна", True),
        "f7": ask_fact("f7 - Вода тепла (цільовий стан)", False),
        "f8": 1  # Крок відкриття завжди = 1
    }

    return state


# Створюємо вирішувач
engine = InferenceEngine(RULES_BASE)

# Запуск із логуванням
with Logger("lab5_shower_system_log.txt"):
    print("=" * 60)
    print("ЛАБОРАТОРНА РОБОТА №5")
    print("ЕКСПЕРТНА СИСТЕМА КЕРУВАННЯ ДУШЕМ")
    print("Продукційне представлення знань")
    print("=" * 60)
    print(f"\nВесь вивід дублюється у файл: 'lab5_shower_system_log.txt'\n")

    # ⭐ ЗАПИТУЄМО КОРИСТУВАЧА ПРО ПОЧАТКОВИЙ СТАН
    initial_state = get_initial_state_from_user()

    print_header("РОБОТА ЕКСПЕРТНОЇ СИСТЕМИ")
    print_facts_legend()

    # ⭐ ЗАПУСКАЄМО СИСТЕМУ З ІНТЕРАКТИВНІСТЮ
    engine.run(initial_state)

    print("\n" + "=" * 60)
    print("РОБОТА ЗАВЕРШЕНО.")
    print(f"Повний звіт збережено у: 'lab5_shower_system_log.txt'")
    print("=" * 60)
