import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import random
import json
import colorsys

# ------------------ Team Class ------------------ #
class Team:
    def __init__(self, name):
        self.name = name
        self.wins = 0
        self.losses = 0
        self.runs_for = 0
        self.runs_against = 0
        self.run_differential = 0
        self.pool = ""

    def to_dict(self):
        return {
            "name": self.name,
            "wins": self.wins,
            "losses": self.losses,
            "runs_for": self.runs_for,
            "runs_against": self.runs_against,
            "run_differential": self.run_differential,
            "pool": self.pool
        }

    @staticmethod
    def from_dict(data):
        t = Team(data["name"])
        t.wins = data["wins"]
        t.losses = data["wins"]
        t.runs_for = data["runs_for"]
        t.runs_against = data["runs_against"]
        t.run_differential = data["run_differential"]
        t.pool = data["pool"]
        return t

# ------------------ Tournament GUI ------------------ #
class TournamentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tournament Manager")
        self.root.geometry("1200x750")

        # Tournament data
        self.teams = []
        self.games = []
        self.pools = {}
        self.pool_count = 5
        self.pool_size = 4
        self.current_file = None

        self.pool_container = None
        self.pool_frames = {}
        self.pool_listboxes = {}
        self.pool_colors = {}
        
        # New: 'Bank' listbox for unassigned teams
        self.bank_listbox = None

        self.drag_data = {"item": None, "source_listbox": None}

        self.create_widgets()
        self.startup_prompt()

    # ------------------ GUI ------------------ #
    def create_widgets(self):
        # --- Menu --- #
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Tournament", command=self.startup_prompt)
        file_menu.add_command(label="Load Tournament", command=self.startup_prompt)
        file_menu.add_command(label="Save Tournament", command=self.save_tournament_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        info_menu = tk.Menu(menubar, tearoff=False)
        menubar.add_cascade(label="Info", menu=info_menu)
        info_menu.add_command(label="Version & License", command=self.show_info)

        # --- Tabs --- #
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.tab_teams = ttk.Frame(self.notebook)
        self.tab_pools = ttk.Frame(self.notebook)
        self.tab_games = ttk.Frame(self.notebook)
        self.tab_seeding = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_teams, text="Teams")
        self.notebook.add(self.tab_pools, text="Pools")
        self.notebook.add(self.tab_games, text="Games")
        self.notebook.add(self.tab_seeding, text="Seeding")

        self.create_team_tab()
        self.create_pool_tab()
        self.create_game_tab()
        self.create_seeding_tab()

    def startup_prompt(self):
        if self.current_file and not messagebox.askyesno("Confirm", "You have an open tournament. Do you want to continue without saving?"):
            return
        
        popup = tk.Toplevel(self.root)
        popup.title("Startup")
        popup.geometry("300x150") # Set size first to get correct dimensions
        popup.transient(self.root)
        popup.grab_set()

        # Center the popup window on the main window
        self.root.update_idletasks()
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        
        popup_width = 300
        popup_height = 150
        
        x = main_x + (main_width // 2) - (popup_width // 2)
        y = main_y + (main_height // 2) - (popup_height // 2)
        
        popup.geometry(f"+{x}+{y}")


        def handle_new():
            popup.destroy()
            self.new_tournament()
            self.current_file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files","*.json")])
            if not self.current_file:
                self.root.quit()
            self._save_to_file()
            self.update_all_views()

        def handle_load():
            popup.destroy()
            self.load_tournament_file()
            if not self.current_file:
                self.root.quit()

        ttk.Label(popup, text="Would you like to start a new tournament or\nload an existing one?", justify=tk.CENTER).pack(pady=10)
        
        button_frame = ttk.Frame(popup)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="New Tournament", command=handle_new).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Load Existing", command=handle_load).pack(side=tk.LEFT, padx=5)
        
        popup.protocol("WM_DELETE_WINDOW", self.root.quit)
        self.root.wait_window(popup)

    def autosave(self):
        if self.current_file:
            self._save_to_file()

    def _save_to_file(self):
        data = {
            "teams":[t.to_dict() for t in self.teams],
            "games":self.games,
            "pool_count":self.pool_count,
            "pool_size":self.pool_size
        }
        with open(self.current_file, "w") as f:
            json.dump(data, f, indent=4)

    def update_all_views(self):
        self.update_team_listbox()
        self.update_game_listbox()
        self.update_all_pool_listboxes()
        self.seeding_listbox.delete(0, tk.END)

    # ------------------ Info Menu ------------------ #
    def show_info(self):
        version_info = "Version: 1.2"
        creator_info = "Creator: Ty Thomasson"
        license_info = (
            "License: This software is not to be used for commercial purposes or distributed "
            "without the creator's permission.\n\n"
            "For questions, please email: thomassonty@gmail.com"
        )
        donations = "Donations are appreciated: Ko-fi.com/tigerty9"
        
        messagebox.showinfo(
            "Version & License",
            f"{version_info}\n\n"
            f"{creator_info}\n\n"
            f"{license_info}\n\n"
            f"{donations}"
        )

    # ------------------ Teams Tab ------------------ #
    def create_team_tab(self):
        frame_top = ttk.Frame(self.tab_teams)
        frame_top.pack(pady=10)

        ttk.Label(frame_top, text="Team Name:").pack(side=tk.LEFT, padx=5)
        self.team_entry = ttk.Entry(frame_top)
        self.team_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_top, text="Add Team", command=self.add_team).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_top, text="Load Demo", command=self.load_demo).pack(side=tk.LEFT, padx=5)

        self.team_listbox = tk.Listbox(self.tab_teams)
        self.team_listbox.pack(fill="both", expand=True, padx=20, pady=10)
        self.team_listbox.bind("<Double-1>", self.rename_team)

        ttk.Button(self.tab_teams, text="Remove Selected Team", command=self.remove_team).pack(pady=5)

    def add_team(self):
        name = self.team_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Team name cannot be empty")
            return
        if any(t.name == name for t in self.teams):
            messagebox.showerror("Error", "Team already exists")
            return
        self.teams.append(Team(name))
        self.team_entry.delete(0, tk.END)
        self.update_team_listbox()
        self.update_all_pool_listboxes()
        self.autosave()

    def remove_team(self):
        selected = self.team_listbox.curselection()
        if not selected: return
        idx = selected[0]
        team_to_remove = self.teams[idx]
        if team_to_remove.pool:
            pool_num = int(team_to_remove.pool.split()[1])
            if pool_num in self.pools and team_to_remove in self.pools[pool_num]:
                self.pools[pool_num].remove(team_to_remove)
        del self.teams[idx]
        self.update_team_listbox()
        self.update_all_pool_listboxes()
        self.update_game_listbox()
        self.autosave()

    def rename_team(self, event):
        idx = self.team_listbox.curselection()[0]
        team = self.teams[idx]
        new_name = simpledialog.askstring("Rename Team", f"Enter new name for {team.name}:")
        if new_name:
            team.name = new_name.strip()
            self.update_team_listbox()
            self.update_all_pool_listboxes()
            self.autosave()

    def update_team_listbox(self):
        self.team_listbox.delete(0, tk.END)
        for t in self.teams:
            self.team_listbox.insert(tk.END, t.name)

    # ------------------ Pools Tab ------------------ #
    def create_pool_tab(self):
        frame_top = ttk.Frame(self.tab_pools)
        frame_top.pack(pady=10)

        ttk.Button(frame_top, text="Random Pools", command=self.random_pools).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_top, text="Clear Pools", command=self.clear_pools).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_top, text="Set Pool Settings", command=self.set_pool_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_top, text="Randomize Remaining", command=self.randomize_remaining).pack(side=tk.LEFT, padx=5)

        self.rebuild_pool_frames()
        self.update_all_pool_listboxes()

    def rebuild_pool_frames(self):
        if self.pool_container:
            self.pool_container.destroy()
        
        self.pool_container = ttk.Frame(self.tab_pools)
        self.pool_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Bank Frame
        bank_frame = ttk.LabelFrame(self.pool_container, text="Bank (Unassigned Teams)")
        bank_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        self.bank_listbox = tk.Listbox(bank_frame)
        self.bank_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.bank_listbox.bind("<Button-1>", self.on_drag_start)
        self.bank_listbox.bind("<B1-Motion>", self.on_drag_motion)
        self.bank_listbox.bind("<ButtonRelease-1>", self.on_drag_release)

        self.pool_frames = {}
        self.pool_listboxes = {}
        self.pool_colors = {}
        
        # Generate visually distinct colors
        hues = [i / self.pool_count for i in range(self.pool_count)]
        for i, h in enumerate(hues):
            self.pool_colors[i + 1] = self.hsv_to_hex(h, 0.5, 0.8)

        for i in range(1, self.pool_count + 1):
            frame = ttk.LabelFrame(self.pool_container, text=f"Pool {i}")
            frame.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
            lb = tk.Listbox(frame)
            lb.pack(fill="both", expand=True, padx=5, pady=5)
            self.pool_frames[i] = frame
            self.pool_listboxes[i] = lb
            lb.bind("<Button-1>", self.on_drag_start)
            lb.bind("<B1-Motion>", self.on_drag_motion)
            lb.bind("<ButtonRelease-1>", self.on_drag_release)

    def hsv_to_hex(self, h, s, v):
        """Converts HSV color to Hex color string."""
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return '#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255))

    def on_drag_start(self, event):
        listbox = event.widget
        selected_index = listbox.nearest(event.y)
        if selected_index >= 0:
            team_text = listbox.get(selected_index)
            team_name = team_text.split(" (")[0] if " (" in team_text else team_text
            self.drag_data["item"] = next((t for t in self.teams if t.name == team_name), None)
            self.drag_data["source_listbox"] = listbox
            listbox.config(cursor="hand2")

    def on_drag_motion(self, event):
        if self.drag_data["item"]:
            target_listbox = self.root.winfo_containing(event.x_root, event.y_root)
            if target_listbox in self.pool_listboxes.values() or target_listbox == self.bank_listbox:
                if target_listbox != self.drag_data["source_listbox"]:
                    self.drag_data["target_listbox"] = target_listbox
                else:
                    self.drag_data["target_listbox"] = None
            else:
                self.drag_data["target_listbox"] = None

    def on_drag_release(self, event):
        if self.drag_data["item"] and "target_listbox" in self.drag_data and self.drag_data["target_listbox"]:
            team_to_move = self.drag_data["item"]
            source_listbox = self.drag_data["source_listbox"]
            target_listbox = self.drag_data["target_listbox"]
            target_pool_name = target_listbox.master.cget("text")

            # Remove from source pool
            if source_listbox != self.bank_listbox:
                source_pool_num = int(source_listbox.master.cget("text").split()[1])
                if team_to_move in self.pools.get(source_pool_num, []):
                    self.pools[source_pool_num].remove(team_to_move)
            
            # Add to target pool
            if target_listbox == self.bank_listbox:
                team_to_move.pool = ""
            else:
                target_pool_num = int(target_pool_name.split()[1])
                if target_pool_num not in self.pools:
                    self.pools[target_pool_num] = []
                self.pools[target_pool_num].append(team_to_move)
                team_to_move.pool = target_pool_name

            self.update_all_pool_listboxes()
            self.update_game_listbox()
            self.autosave()
        
        if self.drag_data.get("source_listbox"):
            self.drag_data["source_listbox"].config(cursor="")
        self.drag_data = {"item": None, "source_listbox": None}
    
    def update_all_pool_listboxes(self):
        # Clear and repopulate the bank listbox
        self.bank_listbox.delete(0, tk.END)
        assigned_teams = set()
        for pool_teams in self.pools.values():
            assigned_teams.update(pool_teams)
        
        unassigned_teams = [t for t in self.teams if t not in assigned_teams]
        
        for t in unassigned_teams:
            self.bank_listbox.insert(tk.END, t.name)

        # Clear and repopulate all pool listboxes
        for pool_num, lb in self.pool_listboxes.items():
            lb.delete(0, tk.END)
            for t in self.pools.get(pool_num, []):
                lb.insert(tk.END, f"{t.name} ({t.wins}-{t.losses}, RD:{t.run_differential})")
                lb.itemconfig(tk.END, {'bg': self.pool_colors.get(pool_num, 'white')})

    def random_pools(self):
        self.clear_pools()
        shuffled = self.teams[:]
        random.shuffle(shuffled)
        
        # Distribute teams evenly using round-robin
        pool_keys = sorted(list(self.pool_listboxes.keys()))
        for i, team in enumerate(shuffled):
            pool_num = pool_keys[i % len(pool_keys)]
            if pool_num not in self.pools:
                self.pools[pool_num] = []
            self.pools[pool_num].append(team)
            team.pool = f"Pool {pool_num}"

        self.generate_pool_games()
        self.update_all_pool_listboxes()
        self.update_game_listbox()
        self.autosave()

    def randomize_remaining(self):
        unassigned_teams = [t for t in self.teams if not t.pool]
        random.shuffle(unassigned_teams)
        
        # Create a list of all pools, including empty ones
        all_pools = [p for p in self.pool_listboxes.keys()]
        
        for team in unassigned_teams:
            # Find the smallest pool and add the team to it
            current_pool_sizes = {pool_num: len(self.pools.get(pool_num, [])) for pool_num in all_pools}
            smallest_pool_num = min(current_pool_sizes, key=current_pool_sizes.get)
            
            if smallest_pool_num not in self.pools:
                self.pools[smallest_pool_num] = []
            
            self.pools[smallest_pool_num].append(team)
            team.pool = f"Pool {smallest_pool_num}"

        self.generate_pool_games()
        self.update_all_pool_listboxes()
        self.update_game_listbox()
        self.autosave()

    def generate_pool_games(self):
        # Reset all stats and games
        for team in self.teams:
            team.wins = 0
            team.losses = 0
            team.runs_for = 0
            team.runs_against = 0
            team.run_differential = 0
        self.games.clear()

        # Generate a round-robin schedule for each pool
        for pool in self.pools.values():
            # A round-robin for 4 teams means 6 games. A round-robin for 3 teams means 3 games.
            # The original request was for 3 games per team, which isn't always possible in a round-robin.
            # I will generate a true round-robin (each team plays every other team once) and provide
            # a note about the game count.
            for i in range(len(pool)):
                for j in range(i + 1, len(pool)):
                    t1, t2 = pool[i], pool[j]
                    s1, s2 = random.randint(0, 10), random.randint(0, 10)
                    self.update_team_stats(t1, t2, s1, s2)
                    self.games.append({"team1": t1.name, "score1": s1, "team2": t2.name, "score2": s2})

    def clear_pools(self):
        for t in self.teams: t.pool = ""
        self.pools = {}
        self.update_all_pool_listboxes()
        self.update_game_listbox()
        self.autosave()

    def set_pool_settings(self):
        pools = simpledialog.askinteger("Pools", "Number of Pools:", initialvalue=self.pool_count)
        size = simpledialog.askinteger("Pool Size", "Number of Teams per Pool:", initialvalue=self.pool_size)
        if pools and size:
            self.pool_count = pools
            self.pool_size = size
            self.rebuild_pool_frames()
            self.clear_pools()
            self.autosave()

    # ------------------ Games Tab ------------------ #
    def create_game_tab(self):
        frame_top = ttk.Frame(self.tab_games)
        frame_top.pack(pady=10)

        ttk.Button(frame_top, text="Add Game", command=self.open_game_popup).pack(side=tk.LEFT, padx=5)

        self.game_listbox = tk.Listbox(self.tab_games)
        self.game_listbox.pack(fill="both", expand=True, padx=20, pady=10)
        self.game_listbox.bind("<Double-1>", self.edit_game_popup)

    def open_game_popup(self, game_data=None, game_index=None):
        popup = tk.Toplevel(self.root)
        popup.title("Add/Edit Game")
        popup.geometry("300x250")
        popup.transient(self.root)
        popup.grab_set()

        ttk.Label(popup, text="Team 1:").pack(pady=5)
        team1_var = tk.StringVar(value=game_data['team1'] if game_data else "")
        team1_cb = ttk.Combobox(popup, values=[t.name for t in self.teams], textvariable=team1_var)
        team1_cb.pack()

        ttk.Label(popup, text="Score:").pack(pady=5)
        score1_var = tk.StringVar(value=str(game_data['score1']) if game_data else "0")
        score1_entry = ttk.Entry(popup, textvariable=score1_var)
        score1_entry.pack()

        ttk.Label(popup, text="Team 2:").pack(pady=5)
        team2_var = tk.StringVar(value=game_data['team2'] if game_data else "")
        team2_cb = ttk.Combobox(popup, values=[t.name for t in self.teams], textvariable=team2_var)
        team2_cb.pack()

        ttk.Label(popup, text="Score:").pack(pady=5)
        score2_var = tk.StringVar(value=str(game_data['score2']) if game_data else "0")
        score2_entry = ttk.Entry(popup, textvariable=score2_var)
        score2_entry.pack()

        def submit_popup():
            t1 = team1_var.get()
            t2 = team2_var.get()
            if not t1 or not t2:
                messagebox.showerror("Error", "Both teams must be selected")
                return
            if t1 == t2:
                messagebox.showerror("Error", "Cannot play against self")
                return
            try:
                s1 = int(score1_var.get())
                s2 = int(score2_var.get())
            except:
                messagebox.showerror("Error", "Scores must be integers")
                return

            team1_obj = next(t for t in self.teams if t.name == t1)
            team2_obj = next(t for t in self.teams if t.name == t2)

            if game_data is not None:
                # Remove old stats before applying new ones
                self.remove_game_stats(game_data)
                
                # Update the existing game entry in place
                self.games[game_index]['team1'] = t1
                self.games[game_index]['score1'] = s1
                self.games[game_index]['team2'] = t2
                self.games[game_index]['score2'] = s2
                
            else:
                # Add a new game
                new_game = {'team1': t1, 'score1': s1, 'team2': t2, 'score2': s2}
                self.games.append(new_game)
                
            self.update_team_stats(team1_obj, team2_obj, s1, s2)
            self.update_game_listbox()
            self.update_all_pool_listboxes()
            self.autosave()
            popup.destroy()

        ttk.Button(popup, text="Submit", command=submit_popup).pack(pady=10)
        popup.bind("<Return>", lambda e: submit_popup())
        self.root.wait_window(popup)

    def edit_game_popup(self, event):
        idx = self.game_listbox.curselection()
        if not idx:
            return
        
        game = self.games[idx[0]]
        self.open_game_popup(game_data=game, game_index=idx[0])

    def remove_game_stats(self, game):
        # Find the teams to update stats
        t1_name = game['team1']
        t2_name = game['team2']
        t1_obj = next((t for t in self.teams if t.name == t1_name), None)
        t2_obj = next((t for t in self.teams if t.name == t2_name), None)

        if not t1_obj or not t2_obj:
            return

        s1, s2 = game['score1'], game['score2']

        t1_obj.runs_for -= s1
        t1_obj.runs_against -= s2
        t2_obj.runs_for -= s2
        t2_obj.runs_against -= s1

        if s1 > s2:
            t1_obj.wins -= 1
            t2_obj.losses -= 1
        elif s2 > s1:
            t2_obj.wins -= 1
            t1_obj.losses -= 1
        
        t1_obj.run_differential = t1_obj.runs_for - t1_obj.runs_against
        t2_obj.run_differential = t2_obj.runs_for - t2_obj.runs_against

    def update_team_stats(self, team1, team2, s1, s2):
        team1.runs_for += s1
        team1.runs_against += s2
        team2.runs_for += s2
        team2.runs_against += s1
        if s1 > s2:
            team1.wins += 1
            team2.losses += 1
        elif s2 > s1:
            team2.wins += 1
            team1.losses += 1
        team1.run_differential = team1.runs_for - team1.runs_against
        team2.run_differential = team2.runs_for - team2.runs_against

    def update_game_listbox(self):
        self.game_listbox.delete(0, tk.END)

        for g in self.games:
            t1_obj = next((t for t in self.teams if t.name == g['team1']), None)
            t2_obj = next((t for t in self.teams if t.name == g['team2']), None)

            if not t1_obj or not t2_obj:
                continue # Skip if a team in the game no longer exists

            pool_color = 'white'
            if t1_obj.pool and "Pool" in t1_obj.pool:
                try:
                    pool_num = int(t1_obj.pool.split()[1])
                    pool_color = self.pool_colors.get(pool_num, 'white')
                except (ValueError, IndexError):
                    pass

            display_text = f"{t1_obj.name} [{g['score1']}] - [{g['score2']}] {t2_obj.name} ({t1_obj.pool})"
            self.game_listbox.insert(tk.END, display_text)
            self.game_listbox.itemconfig(tk.END, {'bg': pool_color})

    def get_team_pool(self, team_name):
        """Helper function to get a team's pool for sorting."""
        team = next((t for t in self.teams if t.name == team_name), None)
        return team.pool if team else ""

    # ------------------ Seeding Tab ------------------ #
    def create_seeding_tab(self):
        ttk.Button(self.tab_seeding, text="Calculate Seeding", command=self.calculate_seeding).pack(pady=10)
        self.seeding_listbox = tk.Listbox(self.tab_seeding)
        self.seeding_listbox.pack(fill="both", expand=True, padx=20, pady=10)
        self.seeding_listbox.bind("<Double-1>", self.show_team_history)

    def calculate_seeding(self):
        sorted_teams = sorted(self.teams, key=lambda t: t.wins, reverse=True)
        seeded = []
        i = 0
        while i < len(sorted_teams):
            group = [sorted_teams[i]]
            j = i + 1
            while j < len(sorted_teams) and sorted_teams[j].wins == sorted_teams[i].wins:
                group.append(sorted_teams[j])
                j += 1
            if len(group) == 2:
                h2h_winner = self.h2h_winner(group[0], group[1])
                if h2h_winner:
                    if h2h_winner == group[0]:
                        seeded.extend(group)
                    else:
                        seeded.extend([group[1], group[0]])
                    i = j
                    continue
            group.sort(key=lambda t: (t.run_differential, -t.runs_against, t.runs_for), reverse=True)
            if len(group) > 1:
                random.shuffle(group)
            seeded.extend(group)
            i = j
        self.seeding_listbox.delete(0, tk.END)
        for idx, t in enumerate(seeded):
            self.seeding_listbox.insert(tk.END, f"Seed {idx+1}: {t.name} ({t.wins}-{t.losses}, RD: {t.run_differential})")

    def h2h_winner(self, t1, t2):
        for g in self.games:
            if (g["team1"] == t1.name and g["team2"] == t2.name):
                if g["score1"] > g["score2"]: return t1
                elif g["score2"] > g["score1"]: return t2
            if (g["team1"] == t2.name and g["team2"] == t1.name):
                if g["score2"] > g["score1"]: return t2
                elif g["score1"] > g["score2"]: return t1
        return None

    def show_team_history(self, event):
        idx = self.seeding_listbox.curselection()
        if not idx:
            return
        line = self.seeding_listbox.get(idx[0])
        team_name = line.split(":")[1].split("(")[0].strip()
        team = next((t for t in self.teams if t.name == team_name), None)
        if not team:
            return
        history = ""
        for g in self.games:
            if g['team1'] == team.name or g['team2'] == team.name:
                other = g['team2'] if g['team1'] == team.name else g['team1']
                score_self = g['score1'] if g['team1'] == team.name else g['score2']
                score_other = g['score2'] if g['team1'] == team.name else g['score1']
                result = "W" if score_self > score_other else "L" if score_self < score_other else "T"
                pool = next((t.pool for t in self.teams if t.name == other), "")
                history += f"{team.name} [{score_self}] - [{score_other}] {other} ({pool}) -> {result}\n"
        messagebox.showinfo(f"{team.name} History", history if history else "No games played")

    # ------------------ Tournament Files ------------------ #
    def new_tournament(self):
        self.teams = []
        self.games = []
        self.clear_pools()
        self.current_file = None
        self.update_all_views()

    def save_tournament_file(self):
        if not self.current_file:
            self.current_file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files","*.json")])
            if not self.current_file: return
        self._save_to_file()
        messagebox.showinfo("Saved", f"Tournament saved to {self.current_file}")

    def load_tournament_file(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
        if not filename:
            return
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                self.teams = [Team.from_dict(d) for d in data.get("teams",[])]
                self.games = data.get("games",[])
                self.pool_count = data.get("pool_count",5)
                self.pool_size = data.get("pool_size",4)
        except (IOError, json.JSONDecodeError):
            messagebox.showerror("Error", "Could not read file.")
            return

        self.current_file = filename
        self.rebuild_pool_frames()
        self.restore_pools_from_teams()
        self.update_all_views()
        messagebox.showinfo("Loaded", f"Tournament loaded from {filename}")

    def restore_pools_from_teams(self):
        self.pools = {}
        for t in self.teams:
            if t.pool and "Pool" in t.pool:
                try:
                    pool_num = int(t.pool.split()[1])
                    if pool_num not in self.pools:
                        self.pools[pool_num] = []
                    self.pools[pool_num].append(t)
                except (ValueError, IndexError):
                    t.pool = ""
                    continue
        self.update_all_pool_listboxes()

    # ------------------ Demo / Defaults ------------------ #
    def load_demo(self):
        if not self.current_file:
            messagebox.showerror("Error", "Please create or load a tournament first.")
            return

        self.teams.clear()
        for i in range(1, 21):
            self.teams.append(Team(f"Team {i}"))
        self.pool_count = 5
        self.pool_size = 4
        self.rebuild_pool_frames()
        self.random_pools()
        self.games.clear()
        for pool in self.pools.values():
            for i in range(len(pool)):
                for j in range(i+1, len(pool)):
                    t1, t2 = pool[i], pool[j]
                    s1, s2 = random.randint(0,10), random.randint(0,10)
                    self.update_team_stats(t1, t2, s1, s2)
                    self.games.append({"team1": t1.name, "score1": s1, "team2": t2.name, "score2": s2})
        self.update_all_views()
        self.autosave()

# ------------------ Main ------------------ #
if __name__ == "__main__":
    root = tk.Tk()
    app = TournamentGUI(root)
    root.mainloop()
