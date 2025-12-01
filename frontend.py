# frontend.py
import customtkinter as ctk
from tkinter import messagebox
from backend import (
    generate_recipe_ai,
    add_recipe_local,
    get_saved_recipes,
    save_recipe_supabase,
    save_user_profile,
    save_user_profile_local,
    fetch_user_profile_local,
    fetch_user_profile_supabase,
    recipe_exists_local,
    recipe_exists_supabase,
    sync_from_supabase_to_local,
    USER_CODE
)

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")


def fx(size, weight="normal"):
    return ("Arial", size, weight)


# MAIN APP
class VegaroApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Vegaro — Eat safely. Cook smart.")
        self.geometry("1200x800")
        self.configure(fg_color="#EFEFEF")

        # Attempt to sync from Supabase on startup
        try:
            profile_remote = fetch_user_profile_supabase()
            if profile_remote is None:
                save_user_profile("", "")
            sync_from_supabase_to_local()
        except Exception:
            pass

        # Load local profile
        self.user_profile = fetch_user_profile_local()

        self.container = ctk.CTkFrame(self, fg_color="#FFFFFF", corner_radius=20)
        self.container.pack(fill="both", expand=True, padx=20, pady=20)

        self.frames = {}
        for F in (HomeScreen, RecipeCreator, RecipeResult, PersonalTab):
            frame = F(self.container, self)
            self.frames[F.__name__] = frame
            frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)

        self.show_frame("HomeScreen")

    def show_frame(self, page):
        self.frames[page].tkraise()

    def navbar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="#FFFFFF", height=70, corner_radius=15)
        bar.pack(side="bottom", fill="x", padx=20, pady=12)

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=10)
        inner.grid_columnconfigure((0, 1), weight=1)

        nav = [
            ("🏠 Home", "HomeScreen"),
            ("👤 Profile", "PersonalTab")
        ]

        for i, (txt, page) in enumerate(nav):
            ctk.CTkButton(
                inner,
                text=txt,
                height=50,
                font=fx(16, "bold"),
                corner_radius=15,
                fg_color="#FFFFFF",
                text_color="#1B4332",
                hover_color="#E8F3EC",
                command=lambda p=page: self.show_frame(p)
            ).grid(row=0, column=i, padx=5, sticky="nsew")


# HOME SCREEN
class HomeScreen(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFFFFF")
        self.controller = controller

        title = ctk.CTkLabel(self, text="Vegaro", font=fx(40, "bold"), text_color="#1B4332")
        title.pack(pady=(40, 5))

        subtitle = ctk.CTkLabel(self, text="Eat safely. Cook smart.", font=fx(18), text_color="#3A5243")
        subtitle.pack(pady=(0, 40))

        ctk.CTkButton(
            self,
            text="🥗 Create a Recipe",
            height=70,
            corner_radius=20,
            font=fx(22, "bold"),
            fg_color="#52B788",
            hover_color="#40916C",
            command=lambda: controller.show_frame("RecipeCreator")
        ).pack(fill="x", padx=100, pady=10)

        ctk.CTkButton(
            self,
            text="💾 View Saved Recipes",
            height=60,
            corner_radius=18,
            font=fx(18, "bold"),
            fg_color="#F1F5F2",
            text_color="#2D6A4F",
            hover_color="#EAF4EA",
            command=lambda: controller.show_frame("RecipeResult")
        ).pack(fill="x", padx=100, pady=10)

        controller.navbar(self)


# RECIPE CREATOR
class RecipeCreator(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFFFFF")
        self.controller = controller

        ctk.CTkLabel(self, text="Create a Recipe", font=fx(26, "bold"), text_color="#1B4332").pack(pady=20)

        ctk.CTkLabel(self, text="What do you have?", font=fx(18, "bold")).pack(pady=(10, 5))
        self.have = ctk.CTkTextbox(self, height=150, corner_radius=12)
        self.have.pack(fill="x", padx=100, pady=5)

        ctk.CTkLabel(self, text="What do you want to eat?", font=fx(18, "bold")).pack(pady=(10, 5))
        self.want = ctk.CTkEntry(self, placeholder_text="e.g., stir-fry noodles", height=50, corner_radius=12)
        self.want.pack(fill="x", padx=100, pady=5)

        ctk.CTkButton(
            self, text="✨ Generate Recipe",
            height=70, corner_radius=18,
            font=fx(20, "bold"),
            fg_color="#FFB703", hover_color="#FF9F1C",
            command=self.make
        ).pack(fill="x", padx=120, pady=20)

        controller.navbar(self)

    def make(self):
        have = self.have.get("1.0", "end").strip()
        want = self.want.get().strip()
        diet = self.controller.user_profile.get("diet", "")
        avoid = self.controller.user_profile.get("allergies", "")

        if not want:
            messagebox.showwarning("Missing Input", "Please enter what you want to eat.")
            return

        try:
            recipe = generate_recipe_ai(want, diet, avoid, have)
        except Exception as e:
            messagebox.showerror("AI Error", str(e))
            return

        result = self.controller.frames["RecipeResult"]
        result.update(recipe)
        self.controller.show_frame("RecipeResult")


# RECIPE RESULT
class RecipeResult(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFFFFF")
        self.controller = controller

        ctk.CTkLabel(self, text="Saved Recipes", font=fx(24, "bold"), text_color="#1B4332").pack(pady=15)

        self.text = ctk.CTkTextbox(self, corner_radius=12)
        self.text.pack(fill="both", expand=True, padx=40, pady=20)

        controller.navbar(self)

    def tkraise(self):
        super().tkraise()
        self.refresh()  

    def refresh(self):
        self.text.delete("1.0", "end")
        recipes = get_saved_recipes()
        if not recipes:
            self.text.insert("1.0", "No saved recipes yet.")
            return

        for i, r in enumerate(reversed(recipes), 1):
            self.text.insert("end", f"=== Recipe {i}: {r['title']} ===\n")
            self.text.insert("end", f"{r['content']}\n\n")

    def update(self, new_recipe=None):
        if new_recipe:
            title = new_recipe.split("\n")[0].strip()[:120]

            if not (recipe_exists_local(title) or recipe_exists_supabase(title)):
                add_recipe_local(title, new_recipe)
                save_recipe_supabase(title, new_recipe)

        self.refresh()


# PROFILE TAB
class PersonalTab(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#FFFFFF")
        self.controller = controller

        ctk.CTkLabel(self, text="Profile", font=fx(26, "bold"), text_color="#1B4332").pack(pady=15)
        ctk.CTkLabel(self, text=f"User Code: {USER_CODE}", font=fx(16, "bold"), text_color="#2D6A4F").pack(pady=10)

        ctk.CTkLabel(self, text="Diet Type:", font=fx(16, "bold")).pack(pady=(10, 5))
        self.diet_combo = ctk.CTkComboBox(self, values=["", "Vegan", "Vegetarian", "Keto", "Halal", "Kosher"],
                                          height=50, corner_radius=12)
        self.diet_combo.pack(fill="x", padx=100, pady=5)

        ctk.CTkLabel(self, text="Allergies:", font=fx(16, "bold")).pack(pady=(10, 5))
        self.allergies_entry = ctk.CTkEntry(self, height=50, corner_radius=12)
        self.allergies_entry.pack(fill="x", padx=100, pady=5)

        ctk.CTkButton(
            self, text="💾 Save Profile",
            font=fx(16, "bold"), height=50,
            corner_radius=15, fg_color="#52B788", hover_color="#40916C",
            command=self.save_profile
        ).pack(pady=20)

        controller.navbar(self)

    def tkraise(self):
        super().tkraise()
        self.load_profile() 

    def load_profile(self):
        try:
            profile_remote = fetch_user_profile_supabase()
        except Exception:
            profile_remote = None

        profile = profile_remote if profile_remote else fetch_user_profile_local()
        self.controller.user_profile.update(profile)
        self.diet_combo.set(profile.get("diet", ""))
        self.allergies_entry.delete(0, "end")
        self.allergies_entry.insert(0, profile.get("allergies", ""))

    def save_profile(self):
        diet = self.diet_combo.get().strip()
        allergies = self.allergies_entry.get().strip()
        self.controller.user_profile.update({"diet": diet, "allergies": allergies})

        save_user_profile_local(diet, allergies)
        remote_res = save_user_profile(diet, allergies)
        if remote_res is None:
            messagebox.showinfo("Saved (local)", "Profile saved locally. Remote save may have failed.")
        else:
            messagebox.showinfo("Saved", "Profile saved locally and remotely.")


if __name__ == "__main__":
    app = VegaroApp()
    app.mainloop()
