import tkinter as tk
from tkinter import ttk
import spacy
import json
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
from PIL import Image, ImageTk


#adding pendulum slider with snap at % levels

# Load SpaCy model for basic NLP analysis
nlp = spacy.load("en_core_web_sm")

# --- Error-resilient loading function ---
def load_json_file(filepath, fallback=None, encoding="utf-8"):
    if fallback is None:
        fallback = []
    try:
        with open(filepath, "r", encoding=encoding) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[!] File not found: {filepath}. Using fallback.")
    except json.JSONDecodeError:
        print(f"[!] JSON decode error in file: {filepath}. Using fallback.")
    except UnicodeDecodeError:
        print(f"[!] Encoding error reading file: {filepath}. Using fallback.")
    return fallback

# --- Load data safely ---
POLARITY_DB = load_json_file("polarity_statements1.json", fallback=[])
QUOTE_BANK = load_json_file("../quote_bank.json", fallback={}, encoding="utf-8")


# Group polarity examples by category
CATEGORY_MAP = {}
for entry in POLARITY_DB:
    axis = entry["axis"]
    if axis not in CATEGORY_MAP:
        CATEGORY_MAP[axis] = []
    CATEGORY_MAP[axis].append(entry)



# Define polarity types and semantic axes
POLARITY_TYPES = {
    "Emphasis-Flip": "Truth hinges on which part is foregrounded",
    "Causal Reversal": "Cause-effect roles are interpreted differently",
    "Moral Anchor Shift": "Shared principle but diverging moral weight",
    "Framing Polarity": "Interpretation based on worldview or identity",
    "Resolution Trap": "Appears neutral but conceals unresolved polarity"
}

SEMANTIC_AXES = [
    "Moral", "Identity", "Cognitive", "Temporal", "Epistemic", "Legal", "Political"
]

# Keywords used for automatic classification
KEYWORDS = {
    "freedom": ("Emphasis-Flip", "Moral"),
    "justice": ("Causal Reversal", "Legal"),
    "unity": ("Resolution Trap", "Identity"),
    "truth": ("Framing Polarity", "Epistemic"),
    "law": ("Moral Anchor Shift", "Legal")
}


TEMPLATES = {
    "Emphasis-Flip": [
        "{X} must be balanced with {Y}.",
        "{X} requires {Y}.",
        "{Y} is the foundation of {X}."
    ],
    "Causal Reversal": [
        "{X} leads to {Y}.",
        "{Y} causes {X}.",
        "Without {X}, we cannot achieve {Y}."
    ],
    "Moral Anchor Shift": [
        "{X} protects our values.",
        "{X} restricts our growth.",
        "{X} preserves our identity."
    ],
    "Framing Polarity": [
        "{X} speaks volumes.",
        "To some, {X} is wisdom; to others, it’s silence.",
        "{X} reveals your true beliefs."
    ],
    "Resolution Trap": [
        "The truth lies somewhere in the middle.",
        "Both sides have a point.",
        "This issue requires compromise."
    ]
}


FILLERS = {
    "X": ["freedom", "justice", "order", "tradition", "progress", "truth"],
    "Y": ["security", "equality", "stability", "change", "identity"]
}

CATEGORY_FILLERS = {
    "Legal": ["justice", "law", "fairness"],
    "Moral": ["freedom", "integrity", "duty"],
    "Epistemic": ["truth", "evidence", "knowledge"],
    "Identity": ["unity", "equality", "culture"],
    "Temporal": ["tradition", "progress", "change"],
    "Political": ["power", "governance", "democracy"],
    "Cognitive": ["belief", "reason", "intuition"]
}






def classify_statement(text):
    doc = nlp(text.lower())
    for token in doc:
        if token.lemma_ in KEYWORDS:
            return True, *KEYWORDS[token.lemma_]
    return False, None, None

def complete_statement(partial):
    if "freedom" in partial.lower():
        return "Freedom must be protected. For some, it means liberty from control; for others, equity of opportunity."
    if "justice" in partial.lower():
        return "Justice delayed is justice denied. Justice must also be fair, not just swift."
    return partial + " ... (incomplete, needs contextual polarity completion)"

def generate_statement():
    return random.choice(POLARITY_DB)["statement"]

class PolarityApp:
    def __init__(self, master):
        self.master = master
        master.title("Polarity Statement Explorer")


        self.left_frame = tk.Frame(master)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)


        tk.Label(self.left_frame, text="Select Category:").pack(pady=10)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(self.left_frame, textvariable=self.category_var, state="readonly")
        self.category_combo["values"] = list(CATEGORY_MAP.keys())
        self.category_combo.bind("<<ComboboxSelected>>", self.update_examples)
        self.category_combo.pack()

        self.example_listbox = tk.Listbox(self.left_frame, height=6, width=50)
        self.example_listbox.pack(pady=5)
        self.example_listbox.bind("<<ListboxSelect>>", self.display_selected_example)

        #self.generate_custom_button = tk.Button(
           # self.left_frame,
          #  text="🔧 Generate New Polarity Statement",
          # command=self.generate_custom_statement        )
        #self.generate_custom_button.pack(pady=(10, 5))

        self.output = tk.Text(self.right_frame, height=13, width=80, font=("Segoe UI", 12))
        self.output.pack()
        self.output.config(padx=10, pady=10, spacing1=4, spacing3=6)

        # Inside __init__ right after self.output is defined:
        tk.Label(self.left_frame, text="📚 Polarity Statement Explorer", font=("Segoe UI", 10, "bold")).pack(pady=(10, 2))

        # Load the image (adjust path as needed)
        image_path = "ps1.png"
        image = Image.open(image_path)
        image = image.resize((180, 180), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(image)

        # Display below the semantic reference box
        self.image_label = tk.Label(self.left_frame, image=self.tk_image)
        self.image_label.image = self.tk_image  # Prevent garbage collection
        self.image_label.pack(pady=(0, 50))  # Adds 10 pixels of padding below the image

        self.quote_display = tk.Text(self.left_frame, height=5, width=40, font=("Segoe UI", 11), wrap=tk.WORD)
        self.quote_display.pack()
        self.quote_display.config(padx=8, pady=6, spacing1=4, spacing3=6, state=tk.DISABLED)

        # Pendulum frame
        # Main pendulum frame with fixed height
        self.pendulum_frame = tk.Frame(self.right_frame, height=180)
        self.pendulum_frame.pack(fill=tk.X, expand=False)
        self.pendulum_frame.pack_propagate(False)

        # Subframe for slider and labels
        self.slider_frame = tk.Frame(self.pendulum_frame)
        self.slider_frame.pack(fill=tk.X, pady=(5, 0))

        self.group_a_label = tk.Label(self.slider_frame, text="← Group A", fg="red", font=("Segoe UI", 10, "bold"))
        self.group_a_label.pack(side=tk.LEFT, padx=10)

        self.slider = tk.Scale(self.slider_frame, from_=0, to=100, orient="horizontal", label="Polarity",
                               command=self.update_pendulum)
        self.slider.set(50)
        self.slider.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.slider.bind("<ButtonRelease-1>", self.on_slider_release)

        self.group_b_label = tk.Label(self.slider_frame, text="Group B →", fg="blue", font=("Segoe UI", 10, "bold"))
        self.group_b_label.pack(side=tk.RIGHT, padx=10)

        # Subframe for matplotlib canvas
        self.canvas_frame = tk.Frame(self.pendulum_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(5.0, 1.0))  # adjust as needed
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def generate_example(self):
        example = generate_statement()
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, f"🧠 Example Polarity Statement:\n{example}\n")

    def update_examples(self, event):
        category = self.category_var.get()
        self.example_listbox.delete(0, tk.END)
        for ex in CATEGORY_MAP.get(category, []):
            self.example_listbox.insert(tk.END, ex["statement"])

    def wrap_text_by_words(self, text, words_per_line=10, indent="  "):
        words = text.split()
        lines = [" ".join(words[i:i + words_per_line]) for i in range(0, len(words), words_per_line)]
        return "\n".join(f"{indent}{line}" for line in lines)

    def display_selected_example(self, event):
        selection = self.example_listbox.curselection()
        if not selection:
            return

        selected_text = self.example_listbox.get(selection[0])

        for entry in POLARITY_DB:
            if entry["statement"] == selected_text:
                self.output.delete("1.0", tk.END)
                self.output.tag_configure("pivot", foreground="red", background="yellow", font=("Segoe UI", 12, "bold"))

                pivots = entry.get("pivots", [])
                statement = entry.get("statement", "")
                axis = entry.get("axis", "[Unknown]")
                p_type = entry.get("type", "[Unknown]")
                pole_a = entry.get("pole_a", "[Not Provided]")
                pole_b = entry.get("pole_b", "[Not Provided]")



                # Render the statement with coloured pivot terms
                self.output.insert(tk.END, f"📌 Polarity Statement:\n")
                for word in statement.split():
                    if word.strip(".,!?").lower() in pivots:
                        self.output.insert(tk.END, word + " ", "pivot")
                    else:
                        self.output.insert(tk.END, word + " ")
                self.output.insert(tk.END, "\n\n")

                self.output.insert(tk.END, f"🔑 Pivot Term(s): {', '.join(pivots) if pivots else '[Not Provided]'}\n")
                self.output.insert(tk.END, f"🔸 Type:  {p_type}\n")
                self.output.insert(tk.END, f"🔸 Axis:  {axis}\n\n")

                self.output.insert(tk.END, f"🧭 Polar Interpretations:\n\n")
                self.output.insert(tk.END, f"  • A: {self.wrap_text_by_words(pole_a, 10)}\n\n")
                self.output.insert(tk.END, f"  • B: {self.wrap_text_by_words(pole_b, 10)}\n")

                # Store for slider quote function
                self.last_axis = axis
                self.last_theme = pivots[0].lower() if pivots else "general"
                self.group_a_label.config(text=f"← {entry.get('group_a', 'Group A')}")
                self.group_b_label.config(text=f"{entry.get('group_b', 'Group B')} →")
                # Update semantic reference box with notes
                self.quote_display.config(state=tk.NORMAL)
                self.quote_display.delete("1.0", tk.END)
                self.quote_display.insert(tk.END, f"📝 Notes:\n\n{entry.get('notes', 'No notes available.')}")
                self.quote_display.config(state=tk.DISABLED)

                break

    def display_pivot_details(self, entry):
        """
        Display detailed polarity information for a given statement entry,
        with color-highlighted pivot terms.
        """
        self.output.delete("1.0", tk.END)
        self.output.tag_configure("pivot", foreground="red", font=("Segoe UI", 12, "bold"))

        statement = entry.get("statement", "[Missing Statement]")
        pivots = entry.get("pivots", [])
        axis = entry.get("axis", "[Unknown]")
        pole_a = entry.get("pole_a", "[Not Provided]")
        pole_b = entry.get("pole_b", "[Not Provided]")

        # Insert preamble
        self.output.insert(tk.END, f"🔀 Pivot Polarity Focus\n\n", "bold")
        self.output.insert(tk.END, f"Phrase: ")

        # Highlight all pivot terms inline
        current_index = "end"
        words = statement.split()
        for word in words:
            clean = word.strip(".,;:!?").lower()
            if clean in pivots:
                self.output.insert(tk.END, f"{word} ", "pivot")
            else:
                self.output.insert(tk.END, f"{word} ")
        self.output.insert(tk.END, f"\n\nAxis: {axis}\n\n")

        # Divergent poles
        self.output.insert(tk.END, f"🎯 Lens A:\n  {pole_a}\n\n")
        self.output.insert(tk.END, f"🎯 Lens B:\n  {pole_b}\n")

        # Optional: feed into pendulum for visualisation
        pivot = pivots[0] if pivots else "pivot"
        self.show_pendulum(pivot, pole_a, pole_b)

    def show_pendulum(self, pivot, lens_a, lens_b):
        # Placeholder: this can be enhanced with matplotlib or Canvas later
        self.output.insert(tk.END, "\n🔁 POLARITY PENDULUM\n")
        self.output.insert(tk.END, f"\n← {lens_a}\n   [ {pivot.upper()} ]\n→ {lens_b}\n")


    def generate_emphasis_flip(self):
        template = random.choice(TEMPLATES["Emphasis-Flip"])
        x = random.choice(FILLERS["X"])
        y = random.choice(FILLERS["Y"])
        return template.replace("{X}", x).replace("{Y}", y)

    """
    def generate_custom_statement(self):
        self.output.delete("1.0", tk.END)

        # Get selected axis or random
        axis = self.category_var.get()
        if not axis:
            axis = random.choice(list(CATEGORY_FILLERS.keys()))

        # Randomly choose polarity type and template
        p_type = random.choice(list(TEMPLATES.keys()))
        template = random.choice(TEMPLATES[p_type])

        x = random.choice(CATEGORY_FILLERS.get(axis, FILLERS["X"]))
        y = random.choice(FILLERS["Y"])

        # Assume pivot is the more central concept — here we use x
        pivot = x.lower()

        # Generate the polarity statement
        statement = template.replace("{X}", x).replace("{Y}", y)

        # Create divergent poles
        if p_type == "Emphasis-Flip":
            pole_a = f"{x.capitalize()} is the goal; {y} supports it."
            pole_b = f"{y.capitalize()} is the priority; {x} must be constrained by it."
        elif p_type == "Causal Reversal":
            pole_a = f"{x.capitalize()} directly causes {y}; control {x} to reduce {y}."
            pole_b = f"{y.capitalize()} is the root cause of {x}; address {y} first."
        elif p_type == "Moral Anchor Shift":
            pole_a = f"{x.capitalize()} is virtuous and upholds shared values."
            pole_b = f"{x.capitalize()} is regressive and limits progress."
        elif p_type == "Framing Polarity":
            pole_a = f"{x.capitalize()} shows depth and restraint."
            pole_b = f"{x.capitalize()} reveals avoidance or weakness."
        elif p_type == "Resolution Trap":
            pole_a = f"Seeking the middle ground affirms shared humanity."
            pole_b = f"Neutrality denies moral clarity and accountability."
        else:
            pole_a = "Perspective A interpretation."
            pole_b = "Perspective B interpretation."

        # Highlight the pivot in the statement
        highlighted = statement.replace(pivot, f"[{pivot.upper()}]")

        # Final output
        output_text = (
            f"⚙️ Generated Polarity Statement:\n\n"
            f"{highlighted}\n\n"
            f"🔑 Pivot Term: {pivot}\n"
            f"🔸 Type: {p_type}\n"
            f"🔸 Axis: {axis}\n\n"
            f"🧭 Polar Interpretations:\n\n"
            f"  • A: {pole_a}\n\n"
            f"  • B: {pole_b}\n"
        )
        

        self.last_theme = pivot
        self.last_axis = axis

        self.output.insert(tk.END, output_text)
        """


    def update_pendulum(self, val):
        val = int(val)
        self.ax.clear()
        self.ax.set_xlim(0, 100)
        self.ax.set_ylim(0, 1)
        self.ax.axis('off')
        self.ax.plot([0, 100], [0.5, 0.5], color='black', linewidth=1)
        triangle_x = [49, 51, 50]
        triangle_y = [0.53, 0.53, 0.58]
        self.ax.fill(triangle_x, triangle_y, color='purple')
        self.ax.text(0, 0.6, "← Pole A", fontsize=12, ha='left', color='red')
        self.ax.text(100, 0.6, "Pole B →", fontsize=12, ha='right', color='blue')
        self.ax.plot(val, 0.5, marker='o', markersize=10, color='orange')
        self.ax.text(val, 0.35, f"{val}%", fontsize=10, ha='center', color='black')
        self.canvas.draw()

    def get_quote_for_slider(self, axis, pivot, slider_value):
        """
        Fetches a matching quote based on axis, pivot, and slider % position.
        """
        try:
            slider_key = str(slider_value)
            return random.choice(QUOTE_BANK[axis][pivot][slider_key])
        except KeyError:
            return "No matching quote found for this polarity context."

    def snap_slider_value(self, val):
        val = int(val)
        snap_points = [0, 25, 50, 75, 100]
        return min(snap_points, key=lambda x: abs(x - val))

    def on_slider_release(self, event):
        current = self.slider.get()
        snapped = self.snap_slider_value(current)
        self.slider.set(snapped)

        # Use the stored axis and pivot term
        axis = getattr(self, "last_axis", "Moral")
        pivot = getattr(self, "last_theme", "general")

        quote = self.get_quote_for_slider(axis, pivot, snapped)

        self.quote_display.config(state=tk.NORMAL)
        self.quote_display.delete("1.0", tk.END)
        self.quote_display.insert(tk.END, f"📜 Quote @ {snapped}%:\n\n{quote}")
        self.quote_display.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x700")
    app = PolarityApp(root)

    icon_path = "ps2br.ico"
    icon_image = Image.open(icon_path)
    icon_photo = ImageTk.PhotoImage(icon_image)
    root.iconphoto(False, icon_photo)

    root.mainloop()
