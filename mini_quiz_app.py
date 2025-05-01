# Bring in all the tools we need: GUI, dialog boxes, random stuff, timing, and reading JSON files
import tkinter as tk
from tkinter import simpledialog, messagebox
import random, time, json

# Load questions and choose 5 random ones for the whole game
all_questions = json.load(open("questions.json", encoding="utf-8"))
shared_quiz_questions = random.sample(all_questions, 5)
difficulty_scores = {"easy": 6, "medium": 8, "hard": 10}

# This is the main class that runs the entire quiz app
class QuizApp:
    def __init__(self, master):
        # Set up the main window and its look
        self.master = master
        master.title("Mini Quiz")
        master.geometry("700x500")
        master.configure(bg="#1e1e1e")

        # Set up game state and main labels/buttons
        self.players, self.scores, self.current_player_index = [], {}, 0
        self.label = tk.Label(master, text="""Welcome to the Quiz!\n\nRules:\n- 5 questions for all players.\n- 20 seconds per question.\n- ≤5s +3 pts, ≤10s +2 pts, ≤15s +1 pt.\n- Score = base + time bonus.""", font=("Arial", 14), wraplength=650, justify="left", fg="white", bg="#1e1e1e")
        self.label.pack(pady=(30, 10))
        self.timer_label = tk.Label(master, font=("Arial", 14), fg="orange", bg="#1e1e1e")
        self.timer_label.pack()

        # Set up answer input options: text box and radio buttons
        self.answer_var = tk.StringVar()
        self.answer_entry = tk.Entry(master, textvariable=self.answer_var, font=("Arial", 14))
        self.radio_buttons = [tk.Radiobutton(master, variable=self.answer_var, font=("Arial", 14), anchor='w', justify='left', fg="white", bg="#1e1e1e", selectcolor="#333333") for _ in range(4)]

        # Buttons for starting quiz and viewing leaderboard history
        self.submit_button = tk.Button(master, text="Start Quiz", font=("Arial", 14), command=self.setup_players, bg="#333333", fg="white")
        self.submit_button.pack(pady=5)
        self.view_history_button = tk.Button(master, text="View History", font=("Arial", 14), command=self.view_leaderboard_history, bg="#333333", fg="white")
        self.view_history_button.pack(pady=5)
        self.feedback_label = tk.Label(master, font=("Arial", 14), fg="#44ff44", bg="#1e1e1e")
        self.feedback_label.pack(pady=10)
        self.timer_id = self.remaining_time = 0

    # Ask how many players are playing and collect their names
    def setup_players(self):
        num_players = simpledialog.askinteger("Players", "How many players?", parent=self.master, minvalue=1, maxvalue=10)
        if num_players:
            self.players, self.scores = [], {}
            for i in range(num_players):
                name = simpledialog.askstring("Player Name", f"Enter name for Player {i + 1}:", parent=self.master)
                if name: self.players.append(name); self.scores[name] = 0
            self.current_player_index = 0
            self.start_countdown(3)

    # Start a 3-second countdown before the game begins
    def start_countdown(self, s):
        self.label.config(text=f"Starting in {s}...")
        self.submit_button.pack_forget()
        self.master.after(1000, self.start_countdown, s - 1) if s > 0 else self.start_quiz_for_player()

    # Set up everything needed to begin a player's turn
    def start_quiz_for_player(self):
        self.view_history_button.pack_forget()
        self.score = self.current_question_index = self.correct_answers_in_a_row = 0
        self.quiz_questions = shared_quiz_questions.copy()
        self.current_player = self.players[self.current_player_index]
        self.label.config(text=f"{self.current_player}, your turn!")
        self.master.after(1000, self.next_question)

    # Show the next question and reset the interface for it
    def next_question(self):
        self.answer_entry.pack_forget()
        [rb.pack_forget() for rb in self.radio_buttons]
        if self.current_question_index < len(self.quiz_questions):
            self.current = self.quiz_questions[self.current_question_index]
            self.label.config(text=f"{self.current_player}, Q{self.current_question_index+1}: {self.current['question']}")
            self.answer_var.set("")
            self.start_time = time.time()
            if self.current["type"] == "fill": self.answer_entry.pack(pady=5)
            else:
                for i, opt in enumerate(self.current.get("options", [])):
                    self.radio_buttons[i].config(text=opt, value=opt[0]); self.radio_buttons[i].pack(anchor='w', padx=20)
            self.submit_button.config(text="Submit", command=self.check_answer)
            self.submit_button.pack(pady=5)
            self.remaining_time = 20
            self.update_timer()
        else: self.end_turn()

    # Show the countdown timer and update every second
    def update_timer(self):
        self.timer_label.config(text=f"Time left: {self.remaining_time} seconds")
        self.remaining_time -= 1
        self.timer_id = self.master.after(1000, self.update_timer) if self.remaining_time >= 0 else self.auto_skip_question()

    # If the player runs out of time, move to the next question
    def auto_skip_question(self):
        self.submit_button.config(state="disabled")
        self.feedback_label.config(text="Time's up! Moving to next question.")
        self.timer_label.config(text="")
        self.current_question_index += 1
        self.master.after(1500, self.resume_quiz)

    # Check the player’s answer and calculate score
    def check_answer(self):
        if self.timer_id: self.master.after_cancel(self.timer_id)
        self.submit_button.config(state="disabled")
        self.timer_label.config(text="")
        ans = self.answer_var.get().strip().upper()
        time_taken = time.time() - self.start_time
        base = difficulty_scores.get(self.current["difficulty"], 6)
        bonus = 3 if time_taken <= 5 else 2 if time_taken <= 10 else 1 if time_taken <= 15 else 0
        if ans == self.current["answer"]:
            self.score += base + bonus
            self.feedback_label.config(text=f"Correct! +{base} base +{bonus} time")
        else:
            self.feedback_label.config(text=f"Wrong! Correct: {self.current['answer']}")
        self.current_question_index += 1
        self.master.after(1500, self.resume_quiz)

    # Load the next question after checking or skipping
    def resume_quiz(self):
        self.submit_button.config(state="normal")
        self.feedback_label.config(text="")
        self.timer_label.config(text="")
        self.next_question()

    # Switch to the next player or end the game
    def end_turn(self):
        self.scores[self.current_player] = self.score
        self.current_player_index += 1
        self.submit_button.pack_forget()
        if self.current_player_index < len(self.players):
            self.label.config(text=f"Next up: {self.players[self.current_player_index]}...")
            self.master.after(5000, self.start_quiz_for_player)
        else: self.show_leaderboard()

    # Show final scores, save them to file, and reset the game
    def show_leaderboard(self):
        self.view_history_button.pack(pady=5)
        try:
            json.dump({"players": self.players, "scores": self.scores, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}, open("leaderboard.jsonl", "a", encoding="utf-8")); open("leaderboard.jsonl", "a").write("\n")
        except: pass
        lb = "Leaderboard:\n" + "\n".join(f"{n}: {s} points" for n, s in sorted(self.scores.items(), key=lambda x: x[1], reverse=True))
        messagebox.showinfo("Quiz Finished", lb)
        self.label.config(text="Game Over. Press Start Quiz to play again.")
        self.submit_button.config(text="Start Quiz", command=self.setup_players)
        self.submit_button.pack(pady=5)
        self.answer_var.set(""); self.answer_entry.pack_forget(); [rb.pack_forget() for rb in self.radio_buttons]

    # Load and show leaderboard results from past games
    def view_leaderboard_history(self):
        try:
            with open("leaderboard.jsonl", "r", encoding="utf-8") as f:
                text = "History Leaderboards:\n\n"
                for i, line in enumerate(f.readlines()[-5:], 1):
                    data = json.loads(line)
                    text += f"{i}. {data['timestamp']}\n"
                    text += "\n".join(f"    {n}: {s} pts" for n, s in sorted(data['scores'].items(), key=lambda x: x[1], reverse=True)) + "\n\n"
                messagebox.showinfo("History", text)
        except: messagebox.showinfo("History", "No past leaderboard data found.")

# This launches the app window and runs the main game loop
if __name__ == "__main__":
    root = tk.Tk()
    w, h = 700, 500
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
    QuizApp(root)
    root.mainloop()