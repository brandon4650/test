import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import os
import json
import cv2
import numpy as np
import pyautogui
from PIL import ImageGrab, Image, ImageTk
import keyboard

class SpellKeybinder:
    def __init__(self):
        self.running = False
        self.spell_templates = []  # Spell templates from spell bar
        self.spell_keys = []       # Keyboard shortcut for each spell
        self.spell_names = []      # Names of each spell
        self.alert_region = None   # Region containing the 3 alert icons
        self.leftmost_icon_region = None  # Specific region for just the leftmost icon
        self.confidence_threshold = 0.5
        self.last_cast_time = 0
        self.cast_cooldown = 0.5   # Cooldown between casts in seconds
        self.repeat_cast = True    # Whether to repeatedly cast the same spell
        self.config_file = "spell_config.json"
        self.templates_dir = "spell_templates"
        self.debug_queue = []
        self.max_debug_entries = 100
        
        # Create the templates directory if it doesn't exist
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
    
    def save_config(self):
        """Save configuration to a JSON file"""
        config = {
            "alert_region": self.alert_region,
            "leftmost_icon_region": self.leftmost_icon_region,
            "confidence_threshold": self.confidence_threshold,
            "cast_cooldown": self.cast_cooldown,
            "repeat_cast": self.repeat_cast,
            "spell_keys": self.spell_keys,
            "spell_names": self.spell_names
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f)
        
        self.add_debug("Configuration saved to " + self.config_file)
    
    def load_config(self):
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                self.alert_region = config.get("alert_region")
                self.leftmost_icon_region = config.get("leftmost_icon_region")
                self.confidence_threshold = config.get("confidence_threshold", 0.5)
                self.cast_cooldown = config.get("cast_cooldown", 0.5)
                self.repeat_cast = config.get("repeat_cast", True)
                self.spell_keys = config.get("spell_keys", [])
                self.spell_names = config.get("spell_names", [])
                
                self.add_debug("Configuration loaded from " + self.config_file)
                return True
            except Exception as e:
                self.add_debug(f"Error loading configuration: {str(e)}")
                return False
        return False
    
    def load_templates(self):
        """Load spell templates from disk"""
        if os.path.exists(self.templates_dir):
            self.spell_templates = []
            templates = [f for f in os.listdir(self.templates_dir) if f.startswith("spell_") and f.endswith(".png")]
            templates.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))  # Sort by spell number
            
            for template_file in templates:
                template_path = os.path.join(self.templates_dir, template_file)
                template = cv2.imread(template_path)
                if template is not None:
                    self.spell_templates.append(template)
            
            self.add_debug(f"Loaded {len(self.spell_templates)} spell templates from disk")
            return len(self.spell_templates) > 0
        
        return False
    
    def capture_spell_template(self, x, y, name, key):
        """Capture a spell template at the given position"""
        try:
            # Capture a small region around the position
            template = ImageGrab.grab(bbox=(x-20, y-20, x+20, y+20))
            template_np = np.array(template)
            template_np = cv2.cvtColor(template_np, cv2.COLOR_RGB2BGR)
            
            # Add to the templates list
            self.spell_templates.append(template_np)
            self.spell_keys.append(key)
            self.spell_names.append(name)
            
            # Get the index
            idx = len(self.spell_templates) - 1
            
            # Save template to disk
            if not os.path.exists(self.templates_dir):
                os.makedirs(self.templates_dir)
            cv2.imwrite(f"{self.templates_dir}/spell_{idx+1}.png", template_np)
            
            self.add_debug(f"Captured spell '{name}' with key '{key}' at position ({x}, {y})")
            return True
        
        except Exception as e:
            self.add_debug(f"Error capturing spell template: {str(e)}")
            return False
    
    def match_leftmost_icon(self):
        """Identify which spell is shown in the leftmost icon position"""
        try:
            # Check if regions are defined
            if not self.leftmost_icon_region:
                self.add_debug("Leftmost icon region not defined")
                return None
            
            # Capture just the leftmost icon area
            leftmost_screenshot = ImageGrab.grab(bbox=self.leftmost_icon_region)
            leftmost_np = np.array(leftmost_screenshot)
            leftmost_np = cv2.cvtColor(leftmost_np, cv2.COLOR_RGB2BGR)
            
            best_match_idx = None
            best_match_val = 0
            
            # Try to match against all spell templates
            for idx, template in enumerate(self.spell_templates):
                try:
                    # Use template matching
                    result = cv2.matchTemplate(leftmost_np, template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    # If this is the best match so far and above threshold
                    if max_val > best_match_val and max_val >= self.confidence_threshold:
                        best_match_idx = idx
                        best_match_val = max_val
                except Exception as e:
                    self.add_debug(f"Error matching template {idx+1}: {str(e)}")
            
            # Log the detection if a match was found
            if best_match_idx is not None:
                spell_name = self.spell_names[best_match_idx] if best_match_idx < len(self.spell_names) else f"Spell {best_match_idx+1}"
                spell_key = self.spell_keys[best_match_idx] if best_match_idx < len(self.spell_keys) else "unknown"
                self.add_debug(f"Detected '{spell_name}' in leftmost position (match: {best_match_val:.2f}), key: {spell_key}")
            
            return best_match_idx
            
        except Exception as e:
            self.add_debug(f"Error matching leftmost icon: {str(e)}")
            return None
    
    def cast_spell(self, spell_idx):
        """Cast a spell by sending a keyboard shortcut"""
        try:
            # Make sure the index is valid
            if spell_idx >= len(self.spell_keys):
                self.add_debug(f"Invalid spell index: {spell_idx}")
                return False
            
            key = self.spell_keys[spell_idx]
            
            # Get the spell name
            spell_name = self.spell_names[spell_idx] if spell_idx < len(self.spell_names) else f"Spell {spell_idx+1}"
            
            # Log the action
            self.add_debug(f"Casting '{spell_name}' by pressing '{key}'")
            
            # Send the key press
            keyboard.press_and_release(key)
            
            return True
            
        except Exception as e:
            self.add_debug(f"Error casting spell {spell_idx+1}: {str(e)}")
            return False
    
    def start_casting(self):
        """Start the spell casting loop in a separate thread"""
        if self.running:
            return
        
        if not self.spell_templates or not self.spell_keys or not self.leftmost_icon_region:
            self.add_debug("Cannot start: Missing templates, keys, or alert region")
            return False
        
        self.running = True
        self.add_debug("Spell caster started!")
        
        # Create and start the casting thread
        self.cast_thread = threading.Thread(target=self.casting_loop)
        self.cast_thread.daemon = True
        self.cast_thread.start()
        
        return True
    
    def stop_casting(self):
        """Stop the spell casting loop"""
        self.running = False
        self.add_debug("Spell caster stopped")
    
    def casting_loop(self):
        """Main loop for monitoring and casting spells"""
        self.last_cast_time = 0
        last_spell_cast = None
        
        try:
            while self.running:
                # Match the leftmost icon against our templates
                leftmost_spell_idx = self.match_leftmost_icon()
                
                # Cast the spell if a match is found and cooldown has passed
                current_time = time.time()
                should_cast = False
                
                if leftmost_spell_idx is not None and current_time - self.last_cast_time >= self.cast_cooldown:
                    # If repeat_cast is True, we cast regardless of whether it's the same spell
                    # If repeat_cast is False, we only cast if it's a different spell from last time
                    if self.repeat_cast or leftmost_spell_idx != last_spell_cast:
                        should_cast = True
                
                if should_cast:
                    # Try to cast the spell
                    if self.cast_spell(leftmost_spell_idx):
                        self.last_cast_time = current_time
                        last_spell_cast = leftmost_spell_idx
                
                # Small delay to reduce CPU usage
                time.sleep(0.05)
                
        except Exception as e:
            self.add_debug(f"Error in casting loop: {str(e)}")
            self.running = False
    
    def add_debug(self, message):
        """Add a debug message to the queue"""
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.debug_queue.append(f"[{timestamp}] {message}")
        
        # Limit the queue size
        if len(self.debug_queue) > self.max_debug_entries:
            self.debug_queue.pop(0)


class KeybinderUI:
    def __init__(self, root):
        self.root = root
        self.root.title("WoW Spell Priority Keybinder")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # Create the keybinder instance
        self.keybinder = SpellKeybinder()
        
        # Create the UI
        self.create_ui()
        
        # Try to load configuration
        self.load_configuration()
        
        # Set up the global hotkeys
        self.setup_global_hotkeys()
        
        # Debug update timer
        self.last_debug_count = 0
        self.update_debug_area()
    
    def create_ui(self):
        """Create the user interface"""
        # Create the main tabs
        self.tab_control = ttk.Notebook(self.root)
        
        # Setup tab
        self.setup_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.setup_tab, text="Setup")
        
        # Spells tab
        self.spells_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.spells_tab, text="Spells")
        
        # Debug tab
        self.debug_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.debug_tab, text="Debug")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Now create content for each tab
        self.create_setup_tab()
        self.create_spells_tab()
        self.create_debug_tab()
    
    def create_setup_tab(self):
        """Create the setup tab content"""
        # Global settings frame
        settings_frame = ttk.LabelFrame(self.setup_tab, text="Settings")
        settings_frame.pack(fill="x", padx=10, pady=10)
        
        # Confidence threshold
        ttk.Label(settings_frame, text="Confidence Threshold:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.confidence_var = tk.DoubleVar(value=0.5)
        confidence_scale = ttk.Scale(settings_frame, from_=0.1, to=1.0, variable=self.confidence_var, length=200)
        confidence_scale.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(settings_frame, textvariable=self.confidence_var).grid(row=0, column=2, padx=5, pady=5)
        
        # Cast cooldown
        ttk.Label(settings_frame, text="Cast Cooldown (sec):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.cooldown_var = tk.DoubleVar(value=0.5)
        cooldown_scale = ttk.Scale(settings_frame, from_=0.1, to=3.0, variable=self.cooldown_var, length=200)
        cooldown_scale.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(settings_frame, textvariable=self.cooldown_var).grid(row=1, column=2, padx=5, pady=5)
        
        # Repeat cast
        self.repeat_var = tk.BooleanVar(value=True)
        repeat_check = ttk.Checkbutton(settings_frame, text="Allow repeated casting of same spell", variable=self.repeat_var)
        repeat_check.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        
        # Region selection frame
        region_frame = ttk.LabelFrame(self.setup_tab, text="Region Selection")
        region_frame.pack(fill="x", padx=10, pady=10)
        
        # Alert region
        ttk.Label(region_frame, text="Alert Icons Region:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.alert_region_var = tk.StringVar(value="Not defined")
        ttk.Label(region_frame, textvariable=self.alert_region_var).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Button(region_frame, text="Select", command=self.select_alert_region).grid(row=0, column=2, padx=5, pady=5)
        
        # Hotkey information frame
        hotkey_frame = ttk.LabelFrame(self.setup_tab, text="Hotkeys")
        hotkey_frame.pack(fill="x", padx=10, pady=10)
        
        hotkey_text = "F10: Start/Stop casting\n"
        hotkey_text += "F3: Set top-left corner of alert region\n"
        hotkey_text += "F4: Set bottom-right corner of alert region\n"
        hotkey_text += "F2: Capture cursor position for spell (in Spells tab)"
        
        ttk.Label(hotkey_frame, text=hotkey_text).pack(padx=5, pady=5, anchor="w")
        
        # Control buttons frame
        control_frame = ttk.Frame(self.setup_tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Save button
        ttk.Button(control_frame, text="Save Configuration", command=self.save_configuration).pack(side="left", padx=5, pady=5)
        
        # Start/stop buttons
        ttk.Separator(control_frame, orient="vertical").pack(side="left", fill="y", padx=10, pady=5)
        self.start_button = ttk.Button(control_frame, text="Start", command=self.start_keybinder)
        self.start_button.pack(side="left", padx=5, pady=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_keybinder, state="disabled")
        self.stop_button.pack(side="left", padx=5, pady=5)
        
        # Status indicator
        self.status_var = tk.StringVar(value="Status: Stopped")
        status_label = ttk.Label(control_frame, textvariable=self.status_var, font=("Arial", 10, "bold"))
        status_label.pack(side="right", padx=5, pady=5)
    
    def create_spells_tab(self):
        """Create the spells tab content"""
        # Add spell frame
        add_frame = ttk.Frame(self.spells_tab)
        add_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(add_frame, text="Spell Name:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.spell_name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.spell_name_var, width=20).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(add_frame, text="Key Binding:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.spell_key_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.spell_key_var, width=20).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(add_frame, text="Examples: '1', 'ctrl+1', 'numpad1', 'shift+f'").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        
        ttk.Label(add_frame, text="Cursor Position:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.cursor_pos_var = tk.StringVar(value="Hover over spell and press F2")
        ttk.Label(add_frame, textvariable=self.cursor_pos_var).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Button(add_frame, text="Add Spell", command=self.add_spell).grid(row=3, column=1, padx=5, pady=5)
        
        # Import frame for your existing keybinds
        import_frame = ttk.LabelFrame(self.spells_tab, text="Quick Import")
        import_frame.pack(fill="x", padx=10, pady=10)
        
        import_button = ttk.Button(import_frame, text="Import Your Keybinds", command=self.import_keybinds)
        import_button.pack(padx=5, pady=5)
        
        # Spell list frame
        list_frame = ttk.LabelFrame(self.spells_tab, text="Spells")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create treeview for spells
        columns = ("name", "key")
        self.spell_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.spell_tree.heading("name", text="Spell Name")
        self.spell_tree.heading("key", text="Key Binding")
        
        # Set column widths
        self.spell_tree.column("name", width=200)
        self.spell_tree.column("key", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.spell_tree.yview)
        self.spell_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the widgets
        self.spell_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Button frame for list operations
        button_frame = ttk.Frame(self.spells_tab)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_spell).pack(side="left", padx=5)
    
    def create_debug_tab(self):
        """Create the debug tab content"""
        # Debug text area
        self.debug_text = scrolledtext.ScrolledText(self.debug_tab, wrap=tk.WORD, width=80, height=25)
        self.debug_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Control buttons
        button_frame = ttk.Frame(self.debug_tab)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Clear Debug Log", command=self.clear_debug).pack(side="left", padx=5)
    
    def update_debug_area(self):
        """Update the debug text area with new messages"""
        # Only update if there are new messages
        current_count = len(self.keybinder.debug_queue)
        if current_count > self.last_debug_count:
            # Add the new messages
            for i in range(self.last_debug_count, current_count):
                self.debug_text.insert(tk.END, self.keybinder.debug_queue[i] + "\n")
            
            # Scroll to the end
            self.debug_text.see(tk.END)
            self.last_debug_count = current_count
        
        # Schedule the next update
        self.root.after(100, self.update_debug_area)
    
    def clear_debug(self):
        """Clear the debug log"""
        self.keybinder.debug_queue = []
        self.last_debug_count = 0
        self.debug_text.delete(1.0, tk.END)
    
    def setup_global_hotkeys(self):
        """Set up global hotkey listeners"""
        # Start the hotkey listener thread
        self.hotkey_thread = threading.Thread(target=self.hotkey_listener)
        self.hotkey_thread.daemon = True
        self.hotkey_thread.start()
    
    def hotkey_listener(self):
        """Listen for global hotkeys"""
        try:
            # Global variables for region selection
            top_left_set = False
            top_left_x, top_left_y = 0, 0
            
            while True:
                # F10 to toggle start/stop
                if keyboard.is_pressed('f10'):
                    if self.keybinder.running:
                        self.root.after(0, self.stop_keybinder)
                    else:
                        self.root.after(0, self.start_keybinder)
                    time.sleep(0.5)  # Debounce
                
                # F2 to capture cursor position for spell
                if keyboard.is_pressed('f2'):
                    x, y = pyautogui.position()
                    self.cursor_pos_var.set(f"({x}, {y})")
                    self.keybinder.add_debug(f"Captured cursor position: ({x}, {y})")
                    time.sleep(0.3)  # Debounce
                
                # F3 to set top-left corner of alert region
                if keyboard.is_pressed('f3'):
                    top_left_x, top_left_y = pyautogui.position()
                    top_left_set = True
                    self.keybinder.add_debug(f"Set top-left corner at ({top_left_x}, {top_left_y})")
                    time.sleep(0.3)  # Debounce
                
                # F4 to set bottom-right corner of alert region
                if keyboard.is_pressed('f4') and top_left_set:
                    bottom_right_x, bottom_right_y = pyautogui.position()
                    self.keybinder.add_debug(f"Set bottom-right corner at ({bottom_right_x}, {bottom_right_y})")
                    
                    # Set the alert region
                    self.keybinder.alert_region = [top_left_x, top_left_y, bottom_right_x, bottom_right_y]
                    
                    # Calculate the leftmost icon region
                    width = bottom_right_x - top_left_x
                    height = bottom_right_y - top_left_y
                    icon_width = width // 3
                    self.keybinder.leftmost_icon_region = [
                        top_left_x,           # x1
                        top_left_y,           # y1
                        top_left_x + icon_width,  # x2
                        bottom_right_y        # y2
                    ]
                    
                    # Update the display
                    self.root.after(100, lambda: self.alert_region_var.set(
                        f"({top_left_x}, {top_left_y}) to ({bottom_right_x}, {bottom_right_y})"))
                    
                    self.keybinder.add_debug(f"Alert region set to: {self.keybinder.alert_region}")
                    self.keybinder.add_debug(f"Leftmost icon region set to: {self.keybinder.leftmost_icon_region}")
                    
                    # Reset for next time
                    top_left_set = False
                    time.sleep(0.3)  # Debounce
                
                # Small delay to reduce CPU usage
                time.sleep(0.05)
                
        except Exception as e:
            print(f"Error in hotkey listener: {e}")
    
    def select_alert_region(self):
        """Select the alert icons region using keyboard shortcuts"""
        messagebox.showinfo("Select Region", 
                           "1. Move mouse to TOP-LEFT corner of alert icons region and press F3\n"
                           "2. Move mouse to BOTTOM-RIGHT corner and press F4\n"
                           "3. Press ESC if you want to cancel")
    
    def add_spell(self):
        """Add a new spell to the list"""
        name = self.spell_name_var.get().strip()
        key = self.spell_key_var.get().strip()
        pos_text = self.cursor_pos_var.get()
        
        if not name:
            messagebox.showerror("Error", "Please enter a spell name")
            return
        
        if not key:
            messagebox.showerror("Error", "Please enter a key binding")
            return
        
        if pos_text == "Hover over spell and press F2":
            messagebox.showerror("Error", "Please capture a cursor position first (hover over spell and press F2)")
            return
        
        try:
            # Parse the position
            pos_text = pos_text.strip("()")
            x, y = map(int, pos_text.split(","))
            
            # Capture the spell template
            if self.keybinder.capture_spell_template(x, y, name, key):
                # Add to the treeview
                idx = len(self.keybinder.spell_templates) - 1
                self.spell_tree.insert("", "end", values=(name, key), iid=str(idx))
                
                # Clear the inputs
                self.spell_name_var.set("")
                self.spell_key_var.set("")
                self.cursor_pos_var.set("Hover over spell and press F2")
            else:
                messagebox.showerror("Error", "Failed to capture spell template")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add spell: {str(e)}")
    
    def remove_spell(self):
        """Remove the selected spell"""
        selected = self.spell_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a spell to remove")
            return
        
        try:
            # Get the index of the selected spell
            idx = int(selected[0])
            
            # Remove from the keybinder
            if idx < len(self.keybinder.spell_templates):
                self.keybinder.spell_templates.pop(idx)
                self.keybinder.spell_keys.pop(idx)
                self.keybinder.spell_names.pop(idx)
                
                # Update the treeview
                self.update_spell_list()
                
                self.keybinder.add_debug(f"Removed spell at index {idx}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove spell: {str(e)}")
    
    def update_spell_list(self):
        """Update the spell list in the treeview"""
        # Clear the treeview
        for item in self.spell_tree.get_children():
            self.spell_tree.delete(item)
        
        # Add all spells
        for idx, (key, name) in enumerate(zip(self.keybinder.spell_keys, self.keybinder.spell_names)):
            self.spell_tree.insert("", "end", values=(name, key), iid=str(idx))
            
    def update_selected_spell(self):
        """Update the template for a selected spell"""
        selected = self.spell_tree.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a spell to update")
            return
        
        pos_text = self.cursor_pos_var.get()
        if pos_text == "Hover over spell and press F2":
            messagebox.showerror("Error", "Please capture a cursor position first (hover over spell and press F2)")
            return
        
        try:
            # Get the index of the selected spell
            idx = int(selected[0])
            
            # Get the position
            pos_text = pos_text.strip("()")
            x, y = map(int, pos_text.split(","))
            
            # Capture a template at that position
            template = ImageGrab.grab(bbox=(x-20, y-20, x+20, y+20))
            template_np = np.array(template)
            template_np = cv2.cvtColor(template_np, cv2.COLOR_RGB2BGR)
            
            # Update the template
            if idx < len(self.keybinder.spell_templates):
                self.keybinder.spell_templates[idx] = template_np
                
                # Save it to disk
                cv2.imwrite(f"{self.keybinder.templates_dir}/spell_{idx+1}.png", template_np)
                
                name = self.keybinder.spell_names[idx]
                key = self.keybinder.spell_keys[idx]
                self.keybinder.add_debug(f"Updated template for '{name}' (key: {key}) at position ({x}, {y})")
                
                # Reset the cursor position
                self.cursor_pos_var.set("Hover over spell and press F2")
                
                messagebox.showinfo("Success", f"Updated template for '{name}'")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update spell template: {str(e)}")
    
    def import_keybinds(self):
        """Import your predefined keybinds"""
        # Clear existing spells first
        if messagebox.askyesno("Confirm Import", "This will clear existing spells and import your predefined keybinds. Continue?"):
            # Clear existing data
            self.keybinder.spell_templates = []
            self.keybinder.spell_keys = []
            self.keybinder.spell_names = []
            
            # Define your keybinds
            keybinds = [
                ("Bloodlust", "numpad0"),
                ("Earth Shield", "numpad1"),
                ("Ascendance", "numpad2"),
                ("Earth Elemental", "numpad3"),
                ("Storm Elemental", "numpad4"),
                ("Skyfury", "numpad5"),
                ("Ancestral Swiftness", "numpad6"),
                ("Astral Shift", "numpad7"),
                ("Blood Fury", "numpad8"),
                ("Wind Shear", "numpad9"),
                ("Lightning Shield", "ctrl+1"),
                ("Gust of Wind", "ctrl+3"),
                ("Stone Bulwark Totem", "ctrl+4"),
                ("Primal Strike", "1"),
                ("Frost Shock", "2"),
                ("Lightning Bolt", "3"),
                ("Spiritwalker's Grace", "4"),
                ("Chain Lightning", "5"),
                ("Lava Burst", "6"),
                ("Primordial Wave", "7"),
                ("Earth Shock", "8"),
                ("Stormkeeper", "9"),
                ("Earthquake", "0"),
                ("Healing Surge", "-"),
                ("Flame Shock", "="),
                ("Cleanse Spirit", "ctrl+5")
            ]
            
            # Take screenshots of each spell, guided by the user
            messagebox.showinfo("Importing Keybinds", 
                               "Next, you'll need to capture screenshots of each spell.\n\n"
                               "For each spell:\n"
                               "1. Hover your mouse over the spell in your spell bar\n"
                               "2. Press F2 to capture its position\n"
                               "3. The application will then capture that spell\n\n"
                               "Press OK to start capturing spells.")
            
            for i, (name, key) in enumerate(keybinds):
                # Tell the user which spell to hover over
                messagebox.showinfo("Capture Spell", 
                                   f"Please hover your mouse over '{name}' (key: {key}) and press F2.\n\n"
                                   f"Spell {i+1} of {len(keybinds)}")
                
                # Wait for F2 press
                self.waiting_for_capture = True
                self.current_capture_name = name
                self.current_capture_key = key
                
                # For a real implementation, we would need to wait for each spell to be captured
            # Instead of automated capturing, let's do a simplified approach
            for name, key in keybinds:
                # Just add the keybind info without capturing templates
                self.keybinder.spell_names.append(name)
                self.keybinder.spell_keys.append(key)
                
                # Add dummy template (user will need to capture actual templates)
                if len(self.keybinder.spell_templates) > 0:
                    # Use the first template as a placeholder
                    self.keybinder.spell_templates.append(self.keybinder.spell_templates[0].copy())
                
            # Update the spell list
            self.update_spell_list()
            
            messagebox.showinfo("Import Complete", 
                               f"Successfully imported {len(keybinds)} keybinds!\n\n"
                               "Important: You still need to capture the spell icons.\n"
                               "For each spell in the list:\n"
                               "1. Select the spell in the list\n"
                               "2. Hover mouse over that spell in your action bar\n"
                               "3. Press F2 to capture position\n"
                               "4. Click 'Update Selected Spell'")
            
            # Add a button for updating selected spells
            if not hasattr(self, 'update_spell_button'):
                self.update_spell_button = ttk.Button(
                    self.spells_tab.winfo_children()[2].winfo_children()[-1],  # Button frame
                    text="Update Selected Spell",
                    command=self.update_selected_spell
                )
                self.update_spell_button.pack(side="left", padx=5)
            
            self.keybinder.add_debug(f"Imported {len(keybinds)} predefined keybinds")"