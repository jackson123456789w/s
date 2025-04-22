import tkinter as tk
from tkinter import messagebox
import random
import pyttsx3

# Initialize Text-to-Speech
engine = pyttsx3.init()

# Vocabulary (for translations)
vocab_book = {
    "isn't he": {"cz": "že?", "fr": "n'est-ce pas?"},
    "aren't you": {"cz": "nejsi?", "fr": "n'es-tu pas?"},
    "didn't they": {"cz": "neudělali?", "fr": "n'ont-ils pas?"},
    "won't she": {"cz": "nebude?", "fr": "ne sera-t-elle pas?"},
    "wasn't it": {"cz": "nebylo to?", "fr": "n'était-ce pas?"},
    "doesn't he": {"cz": "ne?", "fr": "n'est-ce pas?"},
    "didn't she": {"cz": "neudělala?", "fr": "n'a-t-elle pas?"},
    "wasn't he": {"cz": "nebyl?", "fr": "n'était-il pas?"},
    "haven't they": {"cz": "ne?", "fr": "n'ont-ils pas?"},
    "can't we": {"cz": "nemůžeme?", "fr": "ne pouvons-nous pas?"}
}

# 30 Sentences
questions = [
    {"sentence": "He's a doctor,", "tag": "isn't he"},
    {"sentence": "You're happy,", "tag": "aren't you"},
    {"sentence": "They didn’t go to school,", "tag": "didn't they"},
    {"sentence": "She will be late,", "tag": "won't she"},
    {"sentence": "It was beautiful,", "tag": "wasn't it"},
    {"sentence": "He drives fast,", "tag": "doesn't he"},
    {"sentence": "She didn’t call you,", "tag": "didn't she"},
    {"sentence": "He was at the party,", "tag": "wasn't he"},
    {"sentence": "They have arrived,", "tag": "haven't they"},
    {"sentence": "We can do it,", "tag": "can't we"},
    {"sentence": "You love pizza,", "tag": "don't you"},
    {"sentence": "She likes books,", "tag": "doesn't she"},
    {"sentence": "He went home early,", "tag": "didn't he"},
    {"sentence": "They weren't late,", "tag": "were they"},
    {"sentence": "It’s raining,", "tag": "isn't it"},
    {"sentence": "We watched a movie,", "tag": "didn't we"},
    {"sentence": "Tom isn’t tired,", "tag": "is he"},
    {"sentence": "Lucy can sing,", "tag": "can't she"},
    {"sentence": "The kids played outside,", "tag": "didn't they"},
    {"sentence": "They had dinner,", "tag": "didn't they"},
    {"sentence": "He isn’t your brother,", "tag": "is he"},
    {"sentence": "She’s a nurse,", "tag": "isn't she"},
    {"sentence": "They don’t like fish,", "tag": "do they"},
    {"sentence": "We should leave now,", "tag": "shouldn't we"},
    {"sentence": "It doesn't matter,", "tag": "does it"},
    {"sentence": "He couldn't swim,", "tag": "could he"},
    {"sentence": "They won't come,", "tag": "will they"},
    {"sentence": "The weather is nice,", "tag": "isn't it"},
    {"sentence": "John and Mary are friends,", "tag": "aren't they"},
    {"sentence": "The exam was hard,", "tag": "wasn't it"},
]

random.shuffle(questions)

# GUI App
class EnglishGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("English Question Tag Game")
        self.score = 0
        self.q_index = 0

        self.question_label = tk.Label(root, text="", font=("Arial", 16))
        self.question_label.pack(pady=20)

        self.options = []
        for i in range(5):
            btn = tk.Button(root, text="", font=("Arial", 14), command=lambda i=i: self.check_answer(i))
            btn.pack(fill="x", padx=50, pady=5)
            self.options.append(btn)

        self.translation_label = tk.Label(root, text="", font=("Arial", 12), fg="gray")
        self.translation_label.pack(pady=10)

        self.next_button = tk.Button(root, text="Next", font=("Arial", 14), command=self.next_question)
        self.next_button.pack(pady=10)

        self.vocab_button = tk.Button(root, text="Vocabulary Book", font=("Arial", 12), command=self.show_vocab)
        self.vocab_button.pack()

        self.speak_button = tk.Button(root, text="Speak", font=("Arial", 12), command=self.speak_sentence)
        self.speak_button.pack(pady=5)

        self.next_question()

    def speak_sentence(self):
        text = self.current_question['sentence'] + " " + self.current_question['tag']
        engine.say(text)
        engine.runAndWait()

    def next_question(self):
        if self.q_index >= 10:
            messagebox.showinfo("Quiz Complete", f"Score: {self.score}/10")
            self.root.quit()
            return

        self.current_question = questions[self.q_index]
        self.q_index += 1
        self.question_label.config(text=self.current_question["sentence"] + " [?]")

        correct = self.current_question["tag"]
        tags = list(vocab_book.keys())
        random.shuffle(tags)
        if correct not in tags[:5]:
            tags[random.randint(0, 4)] = correct
        self.correct_tag = correct

        for i, btn in enumerate(self.options):
            tag = tags[i]
            btn.config(text=f"{tag} (cz: {vocab_book.get(tag, {}).get('cz', '')}, fr: {vocab_book.get(tag, {}).get('fr', '')})")

        self.translation_label.config(text="Select the correct question tag.")

    def check_answer(self, index):
        selected = self.options[index].cget("text").split(" ")[0]
        if selected == self.correct_tag:
            self.score += 1
            messagebox.showinfo("Correct!", "Well done!")
        else:
            messagebox.showerror("Wrong!", f"Correct answer: {self.correct_tag}")
        self.next_question()

    def show_vocab(self):
        vocab_text = "\n".join([f"{k}: CZ → {v['cz']}, FR → {v['fr']}" for k, v in vocab_book.items()])
        messagebox.showinfo("Vocabulary Book", vocab_text)

# Launch the app
root = tk.Tk()
app = EnglishGameApp(root)
root.mainloop()
