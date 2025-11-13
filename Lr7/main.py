import sys
from typing import List, Dict, Set, Any, Optional, Callable


# --- Module for Requirement 4: Screen and "Printer" Output ---

class Logger:
    """
    Redirects stdout to both the console and a log file.
    This simulates the "print to screen and printer" requirement.
    """

    def __init__(self, filename: str):
        self.terminal = sys.stdout
        self.logfile = None
        try:
            self.logfile = open(filename, "w", encoding="utf-8")
        except IOError as e:
            print(f"FATAL: Could not open log file {filename}: {e}")

    def write(self, message: str):
        """Write message to terminal and logfile."""
        self.terminal.write(message)
        if self.logfile:
            self.logfile.write(message)

    def flush(self):
        """Flush both output streams."""
        self.terminal.flush()
        if self.logfile:
            self.logfile.flush()

    def __enter__(self):
        """Start redirecting stdout."""
        sys.stdout = self
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        """Stop redirecting stdout and close the log file."""
        sys.stdout = self.terminal
        if self.logfile:
            self.logfile.close()


# --- Core Expert System Architecture ---

Rule = Dict[str, Any]


class ExpertSystemWithTrust:
    """
    Implements a backward-chaining expert system with an integrated
    Trust Subsystem for "WHY" and "HOW" explanations.
    """

    def __init__(self,
                 rules: List[Rule],
                 questions: Dict[str, str],
                 conclusions: Dict[str, str]):

        self.kb: List[Rule] = rules
        self.fact_questions: Dict[str, str] = questions
        self.conclusion_names: Dict[str, str] = conclusions
        self.wm: Set[str] = set()
        self.goal_stack: List[Dict[str, Any]] = []
        self.fired_rules_log: List[Dict[str, Any]] = []

    def reset(self):
        """Resets the working memory and explanation logs for a new session."""
        print("\n" + "=" * 40)
        print("🔄  Новий сеанс. Пам'ять очищено.")
        print("=" * 40)
        self.wm.clear()
        self.goal_stack = []
        self.fired_rules_log = []

    # --- Requirement 1: Explanation Procedures ---

    def _explain_why(self):
        """
        [Trust Subsystem] Explains "WHY" the system is asking the current question.
        It does this by printing the current goal stack.
        """
        print("\n" + "-" * 10 + " [ПОЯСНЕННЯ 'ЧОМУ?'] " + "-" * 10)
        if not self.goal_stack:
            print("> Це початкове запитання для визначення мети.")
            return

        print("> Я ставлю це запитання, щоб довести ланцюжок:")

        for i, entry in enumerate(reversed(self.goal_stack)):
            indent = "  " * i
            goal_name = self.conclusion_names.get(entry['goal'], entry['goal'])
            rule_name = entry['rule']['name']

            print(f"{indent}🎯 ... щоб довести: '{goal_name}'")
            print(f"{indent}📜 ... за допомогою правила: '{rule_name}'")

        print("-" * (29 + len(" [ПОЯСНЕННЯ 'ЧОМУ?'] ")) + "\n")

    def _explain_how(self, final_goal: str):
        """
        [Trust Subsystem] Explains "HOW" the system reached a conclusion.
        It does this by printing the log of fired rules.
        """
        goal_name = self.conclusion_names.get(final_goal, final_goal)
        print("\n" + "-" * 10 + " [ПОЯСНЕННЯ 'ЯК?'] " + "-" * 10)
        print(f"> Я дійшов висновку '{goal_name}' наступним чином:\n")

        if not self.fired_rules_log:
            print("> Висновок базується лише на фактах, наданих користувачем.")
            print("> Відомі факти:", ", ".join(self.wm))
            print("-" * (27 + len(" [ПОЯСНЕННЯ 'ЯК?'] ")))
            return

        for i, log_entry in enumerate(self.fired_rules_log, 1):
            rule = log_entry['rule']
            facts = log_entry['facts']
            conclusion_name = self.conclusion_names.get(rule['then'], rule['then'])

            print(f"КРОК {i}:")
            print(f"  СПИРАЮЧИСЬ НА: {', '.join(facts)}")
            print(f"  Я ВИКОРИСТАВ ПРАВИЛО: '{rule['name']}'")
            print(f"  ТА ОТРИМАВ ФАКТ: '{conclusion_name}'\n")

        print("> Кінець пояснення.")
        print("-" * (27 + len(" [ПОЯСНЕННЯ 'ЯК?'] ")) + "\n")

    # --- Core System Logic ---

    def _ask_user(self, fact: str) -> bool:
        """
        Handles the user interaction loop, including 'why' requests.
        Returns True if the fact is 'yes', False if 'no'.
        """
        question = self.fact_questions.get(fact, f"чи правда, що '{fact}'")

        while True:
            response = input(f"❓ {question}? (yes/no/why): ").strip().lower()

            if response == 'yes':
                return True
            if response == 'no':
                return False
            if response == 'why':
                self._explain_why()
            else:
                print("Будь ласка, введіть 'yes', 'no' або 'why'.")

    def solve(self, goal: str) -> bool:
        """
        The main backward-chaining inference engine.
        Recursively tries to prove a goal.
        Returns True if the goal is proven, False otherwise.
        """

        # 1. Base Case: Fact is already known
        if goal in self.wm:
            return True

        # 2. Base Case: Goal is a negative fact (e.g., 'not_f2')
        # This handles 'no' answers, turning them into provable facts
        # which is crucial for our error-checking and branching rules.
        if goal.startswith('not_'):
            positive_fact = goal[4:]  # e.g., 'f2'
            if positive_fact in self.wm:
                return False  # 'f2' is true, so 'not_f2' is false

            if positive_fact in self.fact_questions:
                # [Log:...] is removed to make output cleaner
                if self._ask_user(positive_fact):
                    self.wm.add(positive_fact)  # 'f2' is true
                    return False  # so 'not_f2' is false
                else:
                    self.wm.add(goal)  # 'not_f2' is true
                    return True  # so 'not_f2' is true

            # If it's not a question, it can't be proven this way
            # (e.g., 'not_i_base_brewed' would fail here)
            return False

            # 3. Recursive Case: Find rules to prove the goal
        applicable_rules = [r for r in self.kb if r['then'] == goal]

        if not applicable_rules:
            # 4. Base Case: No rules, must be a simple fact to ask
            if goal in self.fact_questions:
                if self._ask_user(goal):
                    self.wm.add(goal)
                    return True
            return False  # Cannot be proven

        # 5. Recursive Step: Try all applicable rules
        for rule in applicable_rules:

            # --- Trust Subsystem Integration (Req 2) ---
            self.goal_stack.append({'rule': rule, 'goal': goal})

            all_premises_true = True
            proven_premises = []

            for premise in rule['if']:
                if not self.solve(premise):
                    all_premises_true = False
                    break
                proven_premises.append(premise)

            self.goal_stack.pop()
            # --- End Integration ---

            if all_premises_true:
                self.wm.add(goal)

                # --- Trust Subsystem Integration (Req 2) ---
                self.fired_rules_log.append({
                    'rule': rule,
                    'facts': proven_premises
                })

                return True  # Goal proven

        return False  # No rule succeeded

    def run(self, goal_list: List[str]):
        """
        Main entry point to start a consultation.
        Tries to solve for any of the goals in the prioritized list.
        """
        print(f"\n--- 🏁 Початок консультації ---")
        print(f"Намагаюся визначити результат...")

        final_conclusion = None

        for goal in goal_list:
            if self.solve(goal):
                final_conclusion = goal
                break  # Stop on the first goal that succeeds

        print("\n" + "=" * 20 + " [РЕЗУЛЬТАТ] " + "=" * 20)
        if final_conclusion:
            conclusion_name = self.conclusion_names.get(final_conclusion, final_conclusion)
            print(f"✅  Висновок: **{conclusion_name}** (факт {final_conclusion})")

            # --- Requirement 3: Testing the Trust Subsystem ---
            while True:
                show_how = input("\n> Бажаєте пояснення 'Як?' (how/no): ").strip().lower()
                if show_how == 'how':
                    self._explain_how(final_conclusion)
                    break
                elif show_how == 'no':
                    print("> Консультацію завершено.")
                    break
                else:
                    print("Введіть 'how' або 'no'.")

        else:
            print("❌  Не вдалося дійти жодного висновку.")
        print("=" * (42 + len(" [РЕЗУЛЬТАТ] ")))


# --- Main execution block ---

if __name__ == "__main__":
    # --- Requirement 4: Setup Logger ---
    with Logger("lab7_coffee_machine_log.txt"):
        print("=" * 60)
        print("ЛАБОРАТОРНА РОБОТА No7")
        print("ПІДСИСТЕМА ДОВІРИ (Адаптивна 'Кавомашина')")
        print("=" * 60)
        print(f"\nВесь вивід дублюється у файл: 'lab7_coffee_machine_log.txt'\n")

        # --- Knowledge Base Definition ---

        # Questions for base facts
        FACT_QUESTIONS: Dict[str, str] = {
            'f1': "Кавомашина увімкнена та готова?",
            'f2': "В резервуарі є вода?",
            'f3': "Контейнер з кавою заповнений?",
            'f4': "Контейнер (чашка/стакан) на місці?",
            'f9': "В капучинаторі є молоко?",
            'f10': "Бажаєте збити молоко в пінку (для капучино)?",
            'f12': "Бажаєте міцну каву (Robusta)? (інакше буде Arabica)",
        }

        # Descriptions for goals and intermediate facts
        CONCLUSIONS: Dict[str, str] = {
            'i_grinding_done': "Виконано помел",
            'i_base_brewed': "Приготована кавова основа",
            'i_milk_heated': "Молоко нагріте",
            'i_milk_frothed': "Молоко збите (пінка)",

            'g_espresso_arabica': "Еспресо (Arabica) готове",
            'g_espresso_robusta': "Еспресо (Robusta) готове",
            'g_cappuccino_arabica': "Капучино (Arabica) готове",
            'g_cappuccino_robusta': "Капучино (Robusta) готове",
            'g_hot_milk': "Гаряче молоко готове",
            'g_milk_foam': "Молочна пінка готова",

            'g_error': "Стан помилки (Немаe ресурсів)"
        }

        # Production Rules
        KB_COFFEE: List[Rule] = [
            # --- Coffee Path ---
            {'name': "R1: Помел",
             'if': ['f1', 'f3', 'f4'], 'then': 'i_grinding_done'},
            {'name': "R2: Заварювання",
             'if': ['i_grinding_done', 'f2'], 'then': 'i_base_brewed'},

            # --- Milk Path ---
            {'name': "R3: Нагрів молока",
             'if': ['f1', 'f9', 'f4'], 'then': 'i_milk_heated'},
            {'name': "R4: Збивання пінки",
             'if': ['i_milk_heated', 'f10'], 'then': 'i_milk_frothed'},

            # --- Final Goal: Cappuccino (Most complex, check first) ---
            {'name': "R6.1: Капучино (Arabica)",
             'if': ['i_base_brewed', 'i_milk_frothed', 'not_f12'], 'then': 'g_cappuccino_arabica'},
            {'name': "R6.2: Капучино (Robusta)",
             'if': ['i_base_brewed', 'i_milk_frothed', 'f12'], 'then': 'g_cappuccino_robusta'},

            # --- Final Goal: Espresso (Medium complexity) ---
            {'name': "R5.1: Еспресо (Arabica)",
             'if': ['i_base_brewed', 'not_f10'], 'then': 'g_espresso_arabica'},
            {'name': "R5.2: Еспресо (Robusta)",
             'if': ['i_base_brewed', 'f10', 'not_f9'], 'then': 'g_espresso_robusta'},  # Robusta if foam fails

            # --- Final Goal: Milk Options (Simple, check last) ---
            # We add 'not_f3' to make these mutually exclusive with coffee goals
            {'name': "R8: Молочна пінка (без кави)",
             'if': ['i_milk_frothed', 'not_f3'], 'then': 'g_milk_foam'},
            {'name': "R7: Гаряче молоко (без кави)",
             'if': ['i_milk_heated', 'not_f10', 'not_f3'], 'then': 'g_hot_milk'},

            # --- Error Handling Rules ---
            {'name': "RErr1: Помилка (Немає води)",
             'if': ['f1', 'f3', 'not_f2'], 'then': 'g_error'},  # Tried to make coffee
            {'name': "RErr2: Помилка (Немає кави)",
             'if': ['f1', 'not_f3', 'not_f9'], 'then': 'g_error'},  # No coffee AND no milk
            {'name': "RErr3: Помилка (Немає молока для пінки)",
             'if': ['f1', 'f10', 'not_f9'], 'then': 'g_error'},  # Wanted foam, no milk
        ]

        # This list defines the order of priority.
        # The system tries to prove the most complex goals first.
        FINAL_GOALS: List[str] = [
            'g_cappuccino_arabica',
            'g_cappuccino_robusta',
            'g_espresso_arabica',
            'g_espresso_robusta',
            'g_milk_foam',
            'g_hot_milk',
            'g_error'  # Fallback goal
        ]

        # --- System Initialization ---
        es = ExpertSystemWithTrust(KB_COFFEE, FACT_QUESTIONS, CONCLUSIONS)

        # --- Main Interactive Loop ---
        # This version runs ONCE, determines the goal based on questions,
        # and then exits, as requested.

        es.run(FINAL_GOALS)  # Run the adaptive consultation

        print("\n" + "=" * 60)
        print("РОБОТУ ЗАВЕРШЕНО.")
        print(f"Повний звіт збережено у: 'lab7_coffee_machine_log.txt'")
        print("=" * 60)