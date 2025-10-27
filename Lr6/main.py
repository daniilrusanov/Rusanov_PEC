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

    def run(self, working_memory):
        """
        Запускає основний цикл роботи вирішувача.
        """
        self.log = []
        self.log_action(f"--- Запуск вирішувача ---")
        self.log_action(f"Початковий стан фактів: {working_memory}")

        iteration = 0
        max_iterations = 10  # Захист від нескінченного циклу

        while iteration < max_iterations:
            iteration += 1
            rule_fired = False
            self.log_action(f"\n===== Ітерація {iteration} =====")

            for rule in self.rules_base:
                self.log_action(f"-> Перевірка правила: {rule.name}")

                # 1. Чи виконується умова блоку P?
                if rule.check_P(working_memory):
                    self.log_action(f"   [P] Умова використання: True")

                    # 2. Чи виконується умова блоку A?
                    if rule.check_A(working_memory):
                        self.log_action(f"   [A] Ядро: True")

                        # 3. Виконання блоку F
                        action_description, new_state = rule.execute_F(working_memory)
                        self.log_action(f"   [F] ВИКОНАНО: {action_description}")
                        working_memory.update(new_state)
                        self.log_action(f"   Новий стан: {working_memory}")

                        rule_fired = True
                        break  # Перехід на початок списку продукцій
                    else:
                        self.log_action(f"   [A] Ядро: False")
                else:
                    self.log_action(f"   [P] Умова використання: False")

            # Якщо жодне правило не спрацювало за ітерацію, завершуємо роботу
            if not rule_fired:
                self.log_action("\n===== Роботу завершено =====")
                self.log_action("Жодне правило не було активовано.")
                break

        if iteration == max_iterations:
            self.log_action("\n===== Роботу зупинено =====")
            self.log_action("Перевищено ліміт ітерацій.")

        self.log_action(f"Кінцевий стан фактів: {working_memory}")
        return self.log

# --- База правил (База продукцій) ---

RULES_BASE = [
    Rule(
        name="№1: Почати помел",
        check_P=lambda wm: (
                not wm["f5"] and not wm["f6"] and not wm["f7"] and not wm["f8"]
        ),
        check_A=lambda wm: (
                wm["f1"] and wm["f2"] and wm["f3"] and wm["f4"]
        ),
        execute_F=lambda wm: ("Розпочато помел", {"f5": True})
    ),
    Rule(
        name="№2: Почати приготування",
        check_P=lambda wm: not wm["f6"] and not wm["f7"],
        check_A=lambda wm: wm["f5"],
        execute_F=lambda wm: ("Розпочато приготування", {"f5": False, "f6": True})
    ),
    Rule(
        name="№3: Завершити приготування",
        check_P=lambda wm: not wm["f7"],
        check_A=lambda wm: wm["f6"],
        execute_F=lambda wm: ("Кава готова!", {"f6": False, "f7": True})
    ),
    Rule(
        name="№4: Встановити помилку",
        check_P=lambda wm: not wm["f8"],
        check_A=lambda wm: wm["f1"] and (not wm["f2"] or not wm["f3"]),
        execute_F=lambda wm: ("Помилка: немає води або кави", {"f8": True})
    )
]

# Створюємо наш "Вирішувач"
engine = InferenceEngine(RULES_BASE)

# --- Демонстрація Сценарію 1 (Успішне приготування) ---
initial_state_1 = {
    "f1": True,  # Живлення увімкнено
    "f2": True,  # Вода є
    "f3": True,  # Кава є
    "f4": True,  # Чашка є
    "f5": False,  # Не меле
    "f6": False,  # Не готує
    "f7": False,  # Кава не готова
    "f8": False  # Помилки немає
}

print("*" * 40)
print("  СЦЕНАРІЙ 1: Успішне приготування")
print("*" * 40)

log1 = engine.run(initial_state_1)
for line in log1:
    print(line)
    time.sleep(0.1)  # Пауза для ілюстрації покрокової роботи

# --- Демонстрація Сценарію 2 (Помилка: немає води) ---
initial_state_2 = {
    "f1": True,  # Живлення увімкнено
    "f2": False,  # Води НЕМАЄ
    "f3": True,  # Кава є
    "f4": True,  # Чашка є
    "f5": False,  # Не меле
    "f6": False,  # Не готує
    "f7": False,  # Кава не готова
    "f8": False  # Помилки немає
}

print("\n" + "*" * 40)
print("  СЦЕНАРІЙ 2: Помилка (немає води)")
print("*" * 40)
# Запускаємо вирішувач та протоколюємо роботу
log2 = engine.run(initial_state_2)
for line in log2:
    print(line)
    time.sleep(0.1)