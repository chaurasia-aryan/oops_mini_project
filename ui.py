import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from PIL import Image, ImageTk
import threading
from db_simple import add_user, verify_user, add_post, get_posts
from cv import play_hand_snake, VideoFilterWindow, MoodDetectorWindow

# rang/theme — app ka look and feel
BG_COLOR = "#f0f2f5"
PRIMARY_COLOR = "#1877f2"
WHITE_COLOR = "#ffffff"
SEPARATOR_COLOR = "#dadde1"
FONT_FAMILY = "Helvetica"
FONT_BOLD = "Helvetica Bold"
GREY_TEXT = "#65676b"


# ek chota helper widget — entry with placeholder text
class PlaceholderEntry(tk.Entry):
    def __init__(self, parent, placeholder, is_password=False, **kwargs):
        super().__init__(parent, **kwargs)
        self.placeholder = placeholder
        self.is_password = is_password
        # style thoda simple aur clean
        self.config(font=("Arial", 12), fg="grey", relief="solid", bd=1)
        self.insert(0, placeholder)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, _):
        # to remove the placeholder if user clicks
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.config(fg="black")
            if self.is_password:
                self.config(show="*")

    def _on_focus_out(self, _):
        # agar kuch nahi likha toh placeholder wapas dikhane ke liye 
        if not self.get():
            self.insert(0, self.placeholder)
            self.config(fg="grey")
            if self.is_password:
                self.config(show="")

    def get_value(self):
        # asli value return karo, placeholder nahi
        val = self.get()
        return "" if val == self.placeholder else val


# multiline text with placeholder (for posts)
class PlaceholderText(tk.Text):
    def __init__(self, parent, placeholder, **kwargs):
        super().__init__(parent, **kwargs)
        self.placeholder = placeholder
        self.config(font=("Arial", 12), fg="grey", relief="flat")
        self.insert("1.0", placeholder)
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, _):
        # agar placeholder hi hai toh clear karo
        if self.get("1.0", "end-1c").strip() == self.placeholder:
            self.delete("1.0", tk.END)
            self.config(fg="black")

    def _on_focus_out(self, _):
        # agar empty hai toh wapas placeholder set karo
        if not self.get("1.0", "end-1c").strip():
            self.insert("1.0", self.placeholder)
            self.config(fg="grey")

    def get_value(self):
        # return real content
        val = self.get("1.0", "end-1c").strip()
        return "" if val == self.placeholder else val


# Signup window
class RegistrationWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Sign Up for TakeBook")
        self.geometry("420x380")
        self.config(bg=WHITE_COLOR)
        self.resizable(False, False)
        # grab_set makes this window modal — user pehle isko close karega
        self.grab_set()

        tk.Label(self, text="Create Account", font=(FONT_BOLD, 22), bg=WHITE_COLOR, fg=PRIMARY_COLOR).pack(pady=15)

        self.email = PlaceholderEntry(self, "Email address")
        self.email.pack(pady=8, ipady=6, fill="x", padx=30)
        self.password = PlaceholderEntry(self, "Password", is_password=True)
        self.password.pack(pady=8, ipady=6, fill="x", padx=30)
        self.confirm = PlaceholderEntry(self, "Confirm password", is_password=True)
        self.confirm.pack(pady=8, ipady=6, fill="x", padx=30)

        tk.Button(self, text="Sign Up", bg="#42b72a", fg="white", font=(FONT_BOLD, 13),
                  relief="flat", cursor="hand2", command=self.signup).pack(pady=20, ipadx=10, ipady=5)

    def signup(self):
        # validate, fir DB mein insert karo
        email = self.email.get_value()
        pw = self.password.get_value()
        cpw = self.confirm.get_value()

        if not email or not pw or not cpw:
            messagebox.showerror("Error", "All fields required.")
            return
        if pw != cpw:
            messagebox.showerror("Error", "Passwords do not match.")
            return
        # db_simple.add_user — returns False agar email pehle se hai
        if add_user(email, pw):
            messagebox.showinfo("Success", "Account created successfully!")
            self.destroy()
        else:
            messagebox.showerror("Error", "Email already registered.")


# Login screen — pehla screen jab app start hota hai
class FacebookLogin:
    def __init__(self, root):
        self.root = root
        self.root.title("TakeBook Login")
        self.root.geometry("400x420")
        self.root.config(bg=BG_COLOR)

        frame = tk.Frame(root, bg=WHITE_COLOR, highlightbackground=SEPARATOR_COLOR, highlightthickness=1)
        frame.pack(padx=20, pady=20, fill="both", expand=True)

        tk.Label(frame, text="takebook", font=(FONT_BOLD, 32), fg=PRIMARY_COLOR, bg=WHITE_COLOR).pack(pady=(20, 10))

        self.email = PlaceholderEntry(frame, "Email", width=30)
        self.email.pack(pady=5, ipady=6)
        self.password = PlaceholderEntry(frame, "Password", is_password=True, width=30)
        self.password.pack(pady=5, ipady=6)

        tk.Button(frame, text="Log In", bg=PRIMARY_COLOR, fg="white", width=30, font=(FONT_BOLD, 12),
                  relief="flat", command=self.login).pack(pady=10, ipady=8)
        tk.Frame(frame, height=1, bg=SEPARATOR_COLOR).pack(fill="x", padx=30, pady=15)
        tk.Button(frame, text="Create New Account", bg="#42b72a", fg="white", font=(FONT_BOLD, 11),
                  relief="flat", command=self.open_signup).pack(pady=5, ipady=8)

    def open_signup(self):
        # simple modal signup
        RegistrationWindow(self.root)

    def login(self):
        # check DB and open main window on success
        email = self.email.get_value()
        pw = self.password.get_value()
        if not email or not pw:
            messagebox.showwarning("Error", "Please enter both fields.")
            return
        if verify_user(email, pw):
            self.root.destroy()
            FacebookHome(email)
        else:
            messagebox.showerror("Error", "Invalid email or password.")


# Main app window — feed + khelo kudo etc.
class FacebookHome:
    def __init__(self, email):
        self.email = email
        self.root = tk.Tk()
        self.root.title("TakeBook - Home")
        self.root.geometry("950x600")
        self.root.config(bg=BG_COLOR)
        self.active_tab = None

        # build layout
        self.create_top_bar()
        self.create_sidebar()
        self.create_feed()
        # default view
        self.show_home()
        self.root.mainloop()

    def create_top_bar(self):
        # top bar with logo left, nav right — stable alignment
        bar = tk.Frame(self.root, bg=WHITE_COLOR, height=60, highlightbackground=SEPARATOR_COLOR, highlightthickness=1)
        bar.pack(fill="x")

        logo = tk.Label(bar, text="takebook", font=(FONT_BOLD, 24), fg=PRIMARY_COLOR, bg=WHITE_COLOR)
        logo.pack(side="left", padx=25)

        nav_frame = tk.Frame(bar, bg=WHITE_COLOR)
        nav_frame.pack(side="right", padx=25)

        menu_items = {"Home": self.show_home, "About": self.show_about, "Khelo Kudo 🎮": self.show_khelo, "Account": self.show_account}
        self.buttons = {}
        for name, func in menu_items.items():
            # labels act as clickable nav items — simple, no extra widgets needed
            btn = tk.Label(nav_frame, text=name, bg=WHITE_COLOR, fg="black", font=(FONT_FAMILY, 12), cursor="hand2")
            # bind click and hover — thoda UX acha lagta hai
            btn.bind("<Button-1>", lambda e, f=func, n=name: self.switch_tab(f, n))
            btn.bind("<Enter>", lambda e, b=btn: b.config(fg=PRIMARY_COLOR))
            btn.bind("<Leave>", lambda e, b=btn: b.config(fg="black"))
            btn.pack(side="left", padx=15)
            self.buttons[name] = btn

    def create_sidebar(self):
        # left column — static shortcuts
        frame = tk.Frame(self.root, bg=BG_COLOR, width=250)
        frame.place(x=0, y=60, relheight=1)
        tk.Label(frame, text=f"👤 {self.email}", bg=BG_COLOR, font=(FONT_BOLD, 12)).pack(pady=15, padx=15, anchor="w")
        for icon, txt in {"🧑‍🤝‍🧑": "Friends", "👥": "Groups", "📺": "Watch", "🕒": "Memories"}.items():
            tk.Label(frame, text=f"{icon}  {txt}", bg=BG_COLOR, font=(FONT_FAMILY, 12)).pack(pady=8, padx=15, anchor="w")

    def create_feed(self):
        # main dynamic area where pages are rendered
        self.feed_frame = tk.Frame(self.root, bg=BG_COLOR)
        self.feed_frame.place(x=260, y=70, width=670, height=510)

    def switch_tab(self, func, name):
        # reset nav visuals
        for btn in self.buttons.values():
            btn.config(fg="black", font=(FONT_FAMILY, 12))
        # highlight selected tab
        if name in self.buttons:
            self.buttons[name].config(fg=PRIMARY_COLOR, font=(FONT_BOLD, 12))
        # clear feed and call the selected view
        for w in self.feed_frame.winfo_children():
            w.destroy()
        func()

    # HOME: show post box and feed
    def show_home(self):
        tk.Label(self.feed_frame, text="Home Feed", font=(FONT_BOLD, 16), bg=BG_COLOR).pack(pady=10)
        self.create_post_box()
        posts = get_posts()
        if not posts:
            tk.Label(self.feed_frame, text="No posts yet.", bg=BG_COLOR, fg=GREY_TEXT).pack(pady=30)
        for author, content, img, time in posts:
            self.display_post(author, content, img, time)

    def create_post_box(self):
        # small white card to write a post
        f = tk.Frame(self.feed_frame, bg=WHITE_COLOR, highlightbackground=SEPARATOR_COLOR, highlightthickness=1)
        f.pack(pady=10, padx=10, fill="x")
        text = PlaceholderText(f, f"What's on your mind, {self.email.split('@')[0]}?", height=3)
        text.pack(pady=10, padx=15, fill="x")
        tk.Button(f, text="Post", bg=PRIMARY_COLOR, fg="white", font=(FONT_BOLD, 11),
                  command=lambda: self.submit_post(text)).pack(pady=(5, 10))

    def submit_post(self, text_box):
        # save post to DB, optional image
        content = text_box.get_value()
        if not content:
            messagebox.showwarning("Empty", "Please write something.")
            return
        img_path = None
        if messagebox.askyesno("Add Image", "Do you want to attach an image?"):
            img_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        add_post(self.email, content, img_path)
        # refresh feed; switch_tab keeps nav highlight consistent
        self.switch_tab(self.show_home, "Home")

    def display_post(self, author, content, image, created):
        # render one post card — author, time, text, optional image
        post = tk.Frame(self.feed_frame, bg=WHITE_COLOR, highlightbackground=SEPARATOR_COLOR, highlightthickness=1)
        post.pack(pady=8, padx=10, fill="x")
        tk.Label(post, text=author, font=(FONT_BOLD, 12), bg=WHITE_COLOR).pack(anchor="w", padx=15, pady=(8, 0))
        tk.Label(post, text=created.split('.')[0], fg=GREY_TEXT, font=("Arial", 9), bg=WHITE_COLOR).pack(anchor="w", padx=15)
        tk.Label(post, text=content, bg=WHITE_COLOR, font=("Arial", 12), wraplength=600, justify="left").pack(anchor="w", padx=15, pady=(5, 10))
        if image:
            try:
                img = Image.open(image)
                img.thumbnail((600, 400))
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(post, image=photo, bg=WHITE_COLOR)
                lbl.image = photo
                lbl.pack(padx=15, pady=5)
            except Exception as e:
                # agar image load nahi hua toh console pe print kar denge
                print("Error loading image:", e)

    # Khelo Kudo: games and camera fun
    def show_khelo(self):
        tk.Label(self.feed_frame, text="🎮 Khelo Kudo Zone", font=(FONT_BOLD, 18), bg=BG_COLOR).pack(pady=20)
        # snake game runs in a separate daemon thread so UI doesn't freeze
        tk.Button(self.feed_frame, text="Play Snake 🐍", bg=PRIMARY_COLOR, fg="white", font=(FONT_BOLD, 12),
                  command=lambda: threading.Thread(target=play_hand_snake, daemon=True).start()).pack(pady=12, ipadx=10, ipady=5)
        # filters open in a Toplevel window
        tk.Button(self.feed_frame, text="Live Filters 🎥", bg="#2ecc71", fg="white", font=(FONT_BOLD, 12),
                  command=lambda: VideoFilterWindow(self.root)).pack(pady=12, ipadx=10, ipady=5)
        # mood detector also in Toplevel — quick demo (smile => Happy)
        tk.Button(self.feed_frame, text="Mood Detector 😊", bg="#ffb74d", fg="black", font=(FONT_BOLD, 12),
                  command=lambda: MoodDetectorWindow(self.root)).pack(pady=12, ipadx=10, ipady=5)

    # About page — short description
    def show_about(self):
        tk.Label(self.feed_frame, text="About TakeBook", font=(FONT_BOLD, 18), bg=BG_COLOR).pack(pady=30)
        tk.Label(self.feed_frame, text="This is a Python-based Facebook clone built using Tkinter and SQLite.",
                 font=(FONT_FAMILY, 12), bg=BG_COLOR).pack(pady=10)

    # Account page — show email and logout
    def show_account(self):
        tk.Label(self.feed_frame, text="Account", font=(FONT_BOLD, 18), bg=BG_COLOR).pack(pady=30)
        tk.Label(self.feed_frame, text=f"Logged in as: {self.email}", bg=BG_COLOR, font=(FONT_FAMILY, 12)).pack(pady=10)
        tk.Button(self.feed_frame, text="Logout", bg="#e74c3c", fg="white",
                  font=(FONT_BOLD, 12), command=self.logout).pack(pady=20, ipadx=10, ipady=5)

    def logout(self):
        # close current window and return to login
        self.root.destroy()
        r = tk.Tk()
        FacebookLogin(r)
        r.mainloop()
