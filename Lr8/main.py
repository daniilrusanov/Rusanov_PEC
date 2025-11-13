import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import List, Dict, Set, Any, Optional, Tuple

# --- 1. CORE EXPERT SYSTEM LOGIC (MODIFIED FOR GUI) ---
# --- (Логіка з ЛР7, але без _ask_user та _explain_why) ---

Rule = Dict[str, Any]


class ExpertSystemWithTrust:
    """
    Implements a backward-chaining expert system with a Trust Subsystem.

    MODIFIED for Lab 8:
    - This version is NOT interactive. It receives all facts (working memory)
      from the GUI at the start.
    - Removed _ask_user() and _explain_why().
    - solve() is modified to rely on the pre-filled working memory.
    - _explain_how() is modified to return a string instead of printing.
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
        """Resets the working memory and explanation logs."""
        self.wm.clear()
        self.goal_stack = []
        self.fired_rules_log = []

    def _explain_how(self, final_goal: str) -> str:
        """
        [Trust Subsystem] Explains "HOW" the system reached a conclusion.
        Returns the explanation as a string.
        """
        goal_name = self.conclusion_names.get(final_goal, final_goal)
        report_lines = []

        report_lines.append("-" * 10 + " [ПОЯСНЕННЯ 'ЯК?'] " + "-" * 10)
        report_lines.append(f"> Висновок '{goal_name}' отримано так:\n")

        if not self.fired_rules_log:
            report_lines.append("> Висновок базується лише на початкових фактах.")
            report_lines.append(f"> Відомі факти: {', '.join(self.wm)}")
            return "\n".join(report_lines)

        for i, log_entry in enumerate(self.fired_rules_log, 1):
            rule = log_entry['rule']
            facts = log_entry['facts']
            conclusion_name = self.conclusion_names.get(rule['then'], rule['then'])

            report_lines.append(f"КРОК {i}:")
            report_lines.append(f"  СПИРАЮЧИСЬ НА: {', '.join(facts)}")
            report_lines.append(f"  Я ВИКОРИСТАВ ПРАВИЛО: '{rule['name']}'")
            report_lines.append(f"  ТА ОТРИМАВ ФАКТ: '{conclusion_name}'\n")

        report_lines.append("> Кінець пояснення.")
        return "\n".join(report_lines)

    def solve(self, goal: str) -> bool:
        """
        The main backward-chaining inference engine (GUI-driven).
        """
        # 1. Base Case: Fact is already known (from toggles or rules)
        if goal in self.wm:
            return True

        # 2. Base Case: Goal is a negative fact (e.g., 'not_f2')
        if goal.startswith('not_'):
            positive_fact = goal[4:]
            # Check if the positive fact is in WM.
            # If 'f2' is in WM, 'not_f2' is False.
            if positive_fact in self.wm:
                return False
            # If 'f2' is NOT in WM, 'not_f2' is True (Closed World Assumption)
            else:
                return True

        # 3. Recursive Case: Find rules to prove the goal
        applicable_rules = [r for r in self.kb if r['then'] == goal]

        if not applicable_rules:
            # 4. Base Case: No rules to prove this goal.
            # If it's a base fact (like 'f1'), it would have been
            # in self.wm if the toggle was on. Since we're here,
            # it must be False.
            return False

        # 5. Recursive Step: Try all applicable rules
        for rule in applicable_rules:
            self.goal_stack.append({'rule': rule, 'goal': goal})
            all_premises_true = True
            proven_premises = []

            for premise in rule['if']:
                if not self.solve(premise):
                    all_premises_true = False
                    break
                proven_premises.append(premise)

            self.goal_stack.pop()

            if all_premises_true:
                self.wm.add(goal)  # Add intermediate fact to WM
                self.fired_rules_log.append({
                    'rule': rule,
                    'facts': proven_premises
                })
                return True

        return False  # No rule succeeded

    def run_consultation(self,
                         initial_wm: Set[str],
                         goal_list: List[str]
                         ) -> Tuple[Optional[str], str]:
        """
        Main entry point for the GUI.
        Receives the initial WM from toggles and runs the engine.
        Returns (final_goal_id, final_goal_name).
        """
        self.reset()
        self.wm = initial_wm  # Load WM from GUI toggles

        final_conclusion_id = None

        for goal in goal_list:
            if self.solve(goal):
                final_conclusion_id = goal
                break  # Stop on the first goal that succeeds

        if final_conclusion_id:
            conclusion_name = self.conclusion_names.get(
                final_conclusion_id, final_conclusion_id
            )
            return final_conclusion_id, f"✅ Висновок: {conclusion_name}"
        else:
            return None, "❌ Не вдалося дійти жодного висновку."


# --- 2. GUI APPLICATION (LAB 8 REQUIREMENT) ---

class CoffeeApp:
    """
    Implements the Tkinter GUI for the Coffee Expert System.
    This class handles all visual elements and event binding.
    """

    def __init__(self, root: tk.Tk, expert_system: ExpertSystemWithTrust, goals: List[str]):
        self.root = root
        self.expert_system = expert_system
        self.final_goals_list = goals
        self.last_goal_id: Optional[str] = None

        # This dict will store the tk.BooleanVar for each toggle
        self.fact_vars: Dict[str, tk.BooleanVar] = {}

        # --- Setup the UI ---
        self.root.title("ЛР №8: GUI для Експертної Системи 'Кавомашина'")
        self.root.geometry("500x550")

        style = ttk.Style()
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"))
        style.configure("TCheckbutton", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("Result.TLabel", font=("Segoe UI", 12, "bold"), padding=10)
        style.configure("Error.Result.TLabel", foreground="red")
        style.configure("Success.Result.TLabel", foreground="green")

        self.create_widgets()

    def create_widgets(self):
        """Creates and packs all GUI components."""

        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill="both", expand=True)

        # --- 1. Title ---
        title_label = ttk.Label(
            main_frame,
            text="Налаштування Кавомашини",
            style="Header.TLabel"
        )
        title_label.pack(pady=(0, 10))

        # --- 2. Toggles Frame ---
        toggles_frame = ttk.LabelFrame(
            main_frame,
            text=" Вхідні факти (Тумблери) ",
            padding="10"
        )
        toggles_frame.pack(fill="x", expand=True, pady=10)

        # Dynamically create a checkbutton (toggle) for each base fact
        for fact_id, question in self.expert_system.fact_questions.items():
            var = tk.BooleanVar(value=True)  # Default to True
            chk = ttk.Checkbutton(
                toggles_frame,
                text=question,
                variable=var,
                style="TCheckbutton"
            )
            chk.pack(anchor="w", padx=5, pady=3)
            self.fact_vars[fact_id] = var

        # --- 3. Control Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)

        self.run_button = ttk.Button(
            button_frame,
            text="Отримати результат",
            command=self.run_consultation,
            style="TButton"
        )
        self.run_button.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.how_button = ttk.Button(
            button_frame,
            text="Пояснити 'Як?'",
            command=self.show_explanation,
            state="disabled"  # Disabled until a result is found
        )
        self.how_button.pack(side="left", expand=True, fill="x", padx=(5, 0))

        # --- 4. Result Display ---
        self.result_label = ttk.Label(
            main_frame,
            text="Натисніть 'Отримати результат'",
            style="Result.TLabel",
            anchor="center"
        )
        self.result_label.pack(fill="x", pady=10)

    def run_consultation(self):
        """
        Event handler for the 'Run' button.
        Gathers facts from toggles and runs the expert system.
        """
        # 1. Build the initial Working Memory from toggles
        initial_wm = set()
        for fact_id, var in self.fact_vars.items():
            if var.get():  # If toggle is ON
                initial_wm.add(fact_id)

        # 2. Run the expert system
        goal_id, result_text = self.expert_system.run_consultation(
            initial_wm,
            self.final_goals_list
        )

        # 3. Store the goal ID for the 'How?' button
        self.last_goal_id = goal_id

        # 4. Update the result label and button states
        self.result_label.config(text=result_text)

        if goal_id:
            self.how_button.config(state="normal")
            if goal_id == "g_error":
                self.result_label.configure(style="Error.Result.TLabel")
            else:
                self.result_label.configure(style="Success.Result.TLabel")
        else:
            self.how_button.config(state="disabled")
            self.result_label.configure(style="Error.Result.TLabel")

    def show_explanation(self):
        """
        Event handler for the 'How?' button.
        Opens a new window with the explanation.
        """
        if not self.last_goal_id:
            return

        # 1. Get the explanation string from the expert system
        explanation_text = self.expert_system._explain_how(self.last_goal_id)

        # 2. Create a new Toplevel window
        expl_window = tk.Toplevel(self.root)
        expl_window.title("Пояснення 'Як?'")
        expl_window.geometry("450x350")

        # 3. Create a scrolled text widget
        text_widget = ScrolledText(
            expl_window,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            padx=10,
            pady=10
        )
        text_widget.pack(fill="both", expand=True)

        # 4. Insert the text and disable editing
        text_widget.insert(tk.END, explanation_text)
        text_widget.config(state="disabled")


# --- 3. MAIN EXECUTION BLOCK ---

if __name__ == "__main__":
    # --- Knowledge Base Definition (Copied from Lab 7) ---

    # Questions for base facts (these will become toggles)
    FACT_QUESTIONS: Dict[str, str] = {
        'f1': "Кавомашина увімкнена та готова?",
        'f2': "В резервуарі є вода?",
        'f3': "Контейнер з кавою заповнений?",
        'f4': "Контейнер (чашка/стакан) на місці?",
        'f9': "В капучинаторі є молоко?",
        'f10': "Бажаєте збити молоко в пінку?",
        'f12': "Бажаєте міцну каву (Robusta)?",
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
        # Coffee Path
        {'name': "R1: Помел",
         'if': ['f1', 'f3', 'f4'], 'then': 'i_grinding_done'},
        {'name': "R2: Заварювання",
         'if': ['i_grinding_done', 'f2'], 'then': 'i_base_brewed'},
        # Milk Path
        {'name': "R3: Нагрів молока",
         'if': ['f1', 'f9', 'f4'], 'then': 'i_milk_heated'},
        {'name': "R4: Збивання пінки",
         'if': ['i_milk_heated', 'f10'], 'then': 'i_milk_frothed'},
        # Final Goal: Cappuccino
        {'name': "R6.1: Капучино (Arabica)",
         'if': ['i_base_brewed', 'i_milk_frothed', 'not_f12'], 'then': 'g_cappuccino_arabica'},
        {'name': "R6.2: Капучино (Robusta)",
         'if': ['i_base_brewed', 'i_milk_frothed', 'f12'], 'then': 'g_cappuccino_robusta'},
        # Final Goal: Espresso
        {'name': "R5.1: Еспресо (Arabica)",
         'if': ['i_base_brewed', 'not_f10'], 'then': 'g_espresso_arabica'},
        {'name': "R5.2: Еспресо (Robusta)",
         'if': ['i_base_brewed', 'f10', 'not_f9'], 'then': 'g_espresso_robusta'},
        # Final Goal: Milk Options
        {'name': "R8: Молочна пінка (без кави)",
         'if': ['i_milk_frothed', 'not_f3'], 'then': 'g_milk_foam'},
        {'name': "R7: Гаряче молоко (без кави)",
         'if': ['i_milk_heated', 'not_f10', 'not_f3'], 'then': 'g_hot_milk'},
        # Error Handling Rules
        {'name': "RErr1: Помилка (Немає води)",
         'if': ['f1', 'f3', 'not_f2'], 'then': 'g_error'},
        {'name': "RErr2: Помилка (Немає кави)",
         'if': ['f1', 'not_f3', 'not_f9'], 'then': 'g_error'},
        {'name': "RErr3: Помилка (Немає молока для пінки)",
         'if': ['f1', 'f10', 'not_f9'], 'then': 'g_error'},
    ]

    # Prioritized list of all possible final goals
    FINAL_GOALS_LIST: List[str] = [
        'g_cappuccino_arabica',
        'g_cappuccino_robusta',
        'g_espresso_arabica',
        'g_espresso_robusta',
        'g_milk_foam',
        'g_hot_milk',
        'g_error'  # Fallback goal
    ]

    # --- System Initialization and GUI Launch ---

    # 1. Initialize the expert system logic
    expert_system = ExpertSystemWithTrust(
        KB_COFFEE,
        FACT_QUESTIONS,
        CONCLUSIONS
    )

    # 2. Create the main Tkinter window
    root_window = tk.Tk()

    # 3. Create the App, passing the window and the logic
    app = CoffeeApp(root_window, expert_system, FINAL_GOALS_LIST)

    # 4. Start the application's main loop
    root_window.mainloop()