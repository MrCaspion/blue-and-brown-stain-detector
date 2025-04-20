import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
import json
import os
import sys
from skimage.color import rgb2hed
from skimage.morphology import opening, disk
from skimage.measure import label, regionprops
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from skimage.filters import threshold_otsu
from scipy import ndimage as ndi

class ToolTip:
    """
    A simple tooltip implementation for Tkinter widgets.
    Displays a text popup when the mouse hovers over a widget.
    """
    
    def __init__(self, widget, text):
        """
        Initialize a tooltip for a widget.
        
        Parameters:
            widget: The Tkinter widget to attach the tooltip to
            text: The text to display in the tooltip
        """
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)
    
    def show(self, event=None):
        """
        Display the tooltip near the widget.
        
        Parameters:
            event: The event that triggered the tooltip (optional)
        """
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 5
        y = self.widget.winfo_rooty()
        
        self.hide()
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.tooltip, 
            text=self.text,
            justify="left",
            background="#ffffcc", 
            foreground="black",
            relief="solid", 
            borderwidth=1,
            wraplength=400,
            font=("Arial", 10)
        )
        label.pack(padx=5, pady=5)
        
        self.tooltip.attributes("-topmost", True)
        
        print(f"Tooltip text: {self.text[:50]}...")
    
    def hide(self, event=None):
        """
        Hide the tooltip.
        
        Parameters:
            event: The event that triggered hiding the tooltip (optional)
        """
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

try:
    from config import *
except ImportError:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(script_dir)
    
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            bundle_dir = sys._MEIPASS
            sys.path.append(bundle_dir)
    elif 'RESOURCEPATH' in os.environ:
        resource_path = os.environ['RESOURCEPATH']
        sys.path.append(resource_path)
        
        if os.path.exists(os.path.join(resource_path, 'config.py')):
            sys.path.insert(0, resource_path)
        elif os.path.exists(os.path.join(resource_path, 'python', 'config.py')):
            sys.path.insert(0, os.path.join(resource_path, 'python'))
    
    try:
        from config import *
    except ImportError:
        if 'RESOURCEPATH' in os.environ:
            resource_path = os.environ['RESOURCEPATH']
            config_path = os.path.join(resource_path, 'config.py')
            
            if os.path.exists(config_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("config", config_path)
                config = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config)
                globals().update({name: getattr(config, name) for name in dir(config) 
                                if not name.startswith('__')})
            else:
                messagebox.showerror("Error", f"Could not find config.py at {config_path}")
                sys.exit(1)
        else:
            messagebox.showerror("Error", "Could not load config.py. Make sure it's in the same directory as this script.")
            sys.exit(1)

PARAM_TOOLTIPS = {
    'h_threshold': """Blue Nuclei Detection Sensitivity

What it does: Controls how sensitive the system is when detecting blue cell nuclei

← Lower value: Detects more blue areas (including faint ones), may include more false positives

→ Higher value: Only detects strong blue stains, might miss lighter stained nuclei""",

    'd_threshold': """Brown Staining Detection Sensitivity

What it does: Controls how sensitive the system is when detecting brown stained spots

← Lower value: Detects more brown areas (including faint signals)

→ Higher value: Only detects strong brown stains, more selective detection""",

    'disk_size': """Noise Filtering Strength

What it does: Controls how aggressively small dots and noise are filtered out

← Lower value: Less filtering (keeps small details), might include noise

→ Higher value: More aggressive filtering, cleaner results but might remove small valid dots""",

    'gaussian_sigma': """Nucleus Separation Sensitivity

What it does: Controls how the system separates adjacent or touching cell nuclei

← Lower value: More likely to split touching nuclei (may oversplit single nuclei)

→ Higher value: More likely to keep touching nuclei as single objects""",

    'min_distance': """Minimum Distance Between Nuclei

What it does: Sets the minimum spacing required between detected nuclei centers

← Lower value: Allows nuclei to be detected very close to each other (may detect single nucleus as multiple)

→ Higher value: Forces more space between detected nuclei (may merge adjacent nuclei)""",

    'min_area_h': """Minimum Blue Nucleus Size

What it does: Sets the minimum size that a blue object must be to count as a nucleus

← Lower value: Counts very small blue dots as nuclei (may include artifacts)

→ Higher value: Only counts larger blue objects as nuclei (may miss small nuclei)""",

    'min_area_d': """Minimum Brown Spot Size

What it does: Sets the minimum size that a brown spot must be to be counted

← Lower value: Counts very small brown specks (may include artifacts)

→ Higher value: Only counts larger brown spots (more selective)""",

    'marker_radius': """Display Dot Size

What it does: Controls the size of the colored dots shown on the result image (visual only)

← Lower value: Smaller dots for visualization (better for crowded images)

→ Higher value: Larger dots for visualization (more visible)"""
}

class DotCounterApp:
    """
    Application for counting and analyzing blue nuclei and brown staining in biological images.
    Provides an interactive interface for parameter adjustment and visualization.
    """
    
    def __init__(self, master=None):
        """
        Initialize the dot counter application.
        
        Parameters:
            master: Parent widget (optional). If None, creates a new Tk root window.
        """
        if master is None:
            self.root = tk.Tk()
            self.root.title("Dot Counter")
            self.manage_root = True
        else:
            self.root = master
            self.manage_root = False
        
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        image_frame = tk.Frame(main_frame)
        image_frame.pack(fill=tk.BOTH, expand=True)
        
        self.orig_canvas = tk.Canvas(image_frame)
        self.orig_canvas.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.canvas = tk.Canvas(image_frame)
        self.canvas.pack(side=tk.LEFT, padx=5, pady=5)
        
        controls = tk.Frame(main_frame)
        controls.pack(pady=8, fill=tk.X)
        
        tk.Button(controls, text="Load Image", command=self.load_image).pack(side=tk.LEFT, padx=5)
        
        self.count_btn = tk.Button(controls, text="Count Blobs", command=self.count_blobs, state=tk.DISABLED)
        self.count_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = tk.Button(controls, text="Reset Parameters", command=self.reset_parameters, state=tk.DISABLED)
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = tk.Button(controls, text="Save Parameters", command=self.save_parameters, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        param_frame = tk.Frame(main_frame)
        param_frame.pack(pady=5, fill=tk.X)
        
        left_params = tk.Frame(param_frame)
        left_params.pack(side=tk.LEFT, fill=tk.Y, expand=True, padx=10)
        
        right_params = tk.Frame(param_frame)
        right_params.pack(side=tk.LEFT, fill=tk.Y, expand=True, padx=10)
        
        self.slider_frames = {}
        self.sliders = {}
        
        left_side_params = ['h_threshold', 'd_threshold', 'disk_size', 'gaussian_sigma']
        right_side_params = ['min_distance', 'min_area_h', 'min_area_d', 'marker_radius']
        
        for param in left_side_params:
            config = PARAM_RANGES[param]
            self._create_slider(
                left_params, param, PARAM_NAMES[param],
                config['min'], config['max'], config['step'], config['length'],
                config.get('default', None)
            )
        
        for param in right_side_params:
            config = PARAM_RANGES[param]
            self._create_slider(
                right_params, param, PARAM_NAMES[param],
                config['min'], config['max'], config['step'], config['length'],
                config.get('default', None)
            )
        
        self.label = tk.Label(main_frame, text="", font=("Arial", 11), justify=tk.LEFT)
        self.label.pack(pady=6)
        
        guide_frame = tk.LabelFrame(main_frame, text="Visual Troubleshooting", padx=10, pady=5)
        guide_frame.pack(fill=tk.X, padx=10, pady=5)
        
        guide_label = tk.Label(guide_frame, text=TROUBLESHOOTING_TIPS, justify=tk.LEFT, anchor="w")
        guide_label.pack(fill=tk.X, padx=5, pady=5)
        
        self.default_params = {param: config.get('default', 0) 
                              for param, config in PARAM_RANGES.items()}
        
        self.root.bind('<Tab>', self.swap_focus)
        self.active_slider = None
        
        self.reset_parameters()
        
        try:
            if os.path.exists(DEFAULT_PARAMS_FILE):
                self.load_parameters()
        except Exception:
            pass
    
    def _create_slider(self, parent, name, label_text, from_val, to_val, resolution, length, default=None):
        """
        Create a slider with a frame and tooltip.
        
        Parameters:
            parent: Parent widget for the slider
            name: Internal parameter name
            label_text: Display label for the slider
            from_val: Minimum slider value
            to_val: Maximum slider value
            resolution: Step size for the slider
            length: Length of the slider widget
            default: Default value (optional)
            
        Returns:
            The created slider widget
        """
        frame = tk.Frame(parent, highlightthickness=2, highlightbackground="gray")
        frame.pack(fill=tk.X, pady=3)
        
        slider = tk.Scale(
            frame, from_=from_val, to=to_val, resolution=resolution, 
            orient=tk.HORIZONTAL, label=label_text, 
            command=self.update_dots, state=tk.DISABLED, length=length
        )
        slider.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        
        if name in PARAM_TOOLTIPS:
            help_button = tk.Button(
                frame, 
                text="?", 
                font=("Arial", 9, "bold"),
                fg="white", 
                bg="blue",
                width=2, 
                height=1,
                cursor="question_arrow",
                relief="raised"
            )
            help_button.pack(side=tk.RIGHT, padx=5, pady=5)
            
            tooltip_text = PARAM_TOOLTIPS[name]
            ToolTip(help_button, tooltip_text)
        
        self.slider_frames[name] = frame
        self.sliders[name] = slider
        
        if default is not None:
            slider.set(default)
        
        slider.bind("<Button-1>", lambda e, n=name: self.focus_slider(n, force=True))
        frame.bind("<Button-1>", lambda e, n=name: self.focus_slider(n, force=True))
        
        return slider
    
    def focus_slider(self, which, force=False):
        """
        Focus on a specific slider and highlight its frame.
        
        Parameters:
            which: Name of the slider to focus
            force: Whether to force focus (default False)
        """
        for frame in self.slider_frames.values():
            frame.config(highlightbackground="gray", highlightthickness=2)
        
        if which in self.slider_frames:
            self.slider_frames[which].config(highlightbackground="blue", highlightthickness=3)
            if force and which in self.sliders:
                self.sliders[which].focus_set()
            self.active_slider = which
    
    def swap_focus(self, event):
        """
        Move focus to the next slider when Tab is pressed.
        
        Parameters:
            event: The keyboard event
            
        Returns:
            "break" to prevent default tab behavior
        """
        slider_names = list(self.sliders.keys())
        if not slider_names:
            return "break"
            
        if self.active_slider in slider_names:
            curr_idx = slider_names.index(self.active_slider)
            next_idx = (curr_idx + 1) % len(slider_names)
        else:
            next_idx = 0
            
        self.focus_slider(slider_names[next_idx], force=True)
        return "break"
    
    def reset_parameters(self):
        """
        Reset all sliders to their default values.
        Updates the display if an image is loaded.
        """
        for name, slider in self.sliders.items():
            if name in self.default_params and slider['state'] != tk.DISABLED:
                slider.set(self.default_params[name])
        
        if hasattr(self, 'orig'):
            self.update_dots(None)
    
    def save_parameters(self):
        """
        Save current parameter values to a JSON file.
        Uses the default parameter file or prompts for a location.
        """
        if not hasattr(self, 'path'):
            messagebox.showerror("Error", "No image loaded")
            return
        
        params = {name: slider.get() for name, slider in self.sliders.items()}
        params['image_path'] = self.path
        
        try:
            with open(DEFAULT_PARAMS_FILE, 'w') as f:
                json.dump(params, f, indent=4)
            messagebox.showinfo("Success", f"Parameters saved to default file")
        except Exception as e:
            save_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                initialdir=os.path.dirname(self.path),
                initialfile=f"{os.path.splitext(os.path.basename(self.path))[0]}_params.json"
            )
            
            if save_path:
                with open(save_path, 'w') as f:
                    json.dump(params, f, indent=4)
                messagebox.showinfo("Success", f"Parameters saved to {save_path}")
                
    def load_parameters(self):
        """
        Load parameters from the default parameters file.
        
        Returns:
            bool: True if parameters were loaded successfully, else False 
        """
        if os.path.exists(DEFAULT_PARAMS_FILE):
            try:
                with open(DEFAULT_PARAMS_FILE, 'r') as f:
                    params = json.load(f)
                
                for name, value in params.items():
                    if name in self.sliders and name != 'image_path':
                        self.sliders[name].set(value)
                
                self.update_dots(None)
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load parameters: {str(e)}")
                return False
        return False
                
    def load_image(self):
        """
        Load an image file and prepare it for processing.
        Sets up canvases, initializes channels, and configures sliders.
        """
        path = filedialog.askopenfilename()
        if not path:
            return
        self.path = path
        self.orig = cv2.imread(path)
        img = Image.open(path)
        
        img.thumbnail((DISPLAY_MAX_WIDTH, DISPLAY_MAX_HEIGHT))
        self.display = img
        dw, dh = img.size
        h, w = self.orig.shape[:2]
        self.sx, self.sy = dw / w, dh / h
        
        self.orig_tkimg = ImageTk.PhotoImage(img)
        self.orig_canvas.config(width=dw, height=dh)
        self.orig_canvas.delete("all")
        self.orig_canvas.create_image(dw//2, dh//2, image=self.orig_tkimg)
        
        self.tkimg = ImageTk.PhotoImage(img)
        self.canvas.config(width=dw, height=dh)
        self.canvas.delete("all")
        self.canvas.create_image(dw//2, dh//2, image=self.tkimg)
        
        rgb = cv2.cvtColor(self.orig, cv2.COLOR_BGR2RGB).astype(np.float64) / 255
        hed = rgb2hed(rgb)
        self.h_chan = hed[:, :, 0]
        self.d_chan = hed[:, :, 2]
        h_min, h_max = self.h_chan.min(), self.h_chan.max()
        d_min, d_max = self.d_chan.min(), self.d_chan.max()
        
        self.sliders['h_threshold'].config(from_=h_min, to=h_max, resolution=(h_max - h_min) / 100, state=tk.NORMAL)
        self.sliders['d_threshold'].config(from_=d_min, to=d_max, resolution=(d_max - d_min) / 100, state=tk.NORMAL)
        
        for slider in self.sliders.values():
            slider.config(state=tk.NORMAL)
        
        self.default_params['h_threshold'] = threshold_otsu(self.h_chan)
        self.default_params['d_threshold'] = threshold_otsu(self.d_chan)
        
        self.reset_parameters()
        
        self.load_parameters()
        
        self.count_btn.config(state=tk.NORMAL)
        self.reset_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.NORMAL)
        
        self.focus_slider('h_threshold', force=True)

    def update_dots(self, val):
        """
        Update the image processing based on current slider values.
        
        Parameters:
            val: Value from the slider that triggered the update (can be None)
        """
        if not hasattr(self, 'orig'):
            return
            
        th_h = self.sliders['h_threshold'].get()
        th_d = self.sliders['d_threshold'].get()
        disk_size = int(self.sliders['disk_size'].get())
        gaussian_sigma = self.sliders['gaussian_sigma'].get()
        min_distance = int(self.sliders['min_distance'].get())
        min_area_h = int(self.sliders['min_area_h'].get())
        min_area_d = int(self.sliders['min_area_d'].get())
        marker_radius = int(self.sliders['marker_radius'].get())
        
        mask_h = opening(self.h_chan > th_h, disk(disk_size))
        mask_d = opening(self.d_chan > th_d, disk(disk_size))
        dt = ndi.distance_transform_edt(mask_h)
        sm = ndi.gaussian_filter(dt, sigma=gaussian_sigma)
        coords = peak_local_max(sm, min_distance=min_distance, labels=mask_h)
        markers = np.zeros_like(dt, dtype=int)
        if coords.size:
            for i, (r, c) in enumerate(coords, start=1):
                markers[r, c] = i
        else:
            r, c = np.unravel_index(np.argmax(sm), sm.shape)
            markers[r, c] = 1
        split = watershed(-sm, markers, mask=mask_h)
        lbl_h = split
        lbl_d = label(mask_d)
        cents_h = [r.centroid for r in regionprops(lbl_h) if r.area > min_area_h]
        cents_d = [r.centroid for r in regionprops(lbl_d) if r.area > min_area_d]
        disp = np.array(self.display)
        disp_bgr = cv2.cvtColor(disp, cv2.COLOR_RGB2BGR)
        for y, x in cents_h:
            dx, dy = int(x * self.sx), int(y * self.sy)
            cv2.circle(disp_bgr, (dx, dy), marker_radius, (255, 0, 0), -1)
        for y, x in cents_d:
            dx, dy = int(x * self.sx), int(y * self.sy)
            cv2.circle(disp_bgr, (dx, dy), marker_radius, (0, 0, 255), -1)
        ann = cv2.cvtColor(disp_bgr, cv2.COLOR_BGR2RGB)
        pil_ann = Image.fromarray(ann)
        self.tkimg = ImageTk.PhotoImage(pil_ann)
        self.canvas.config(width=pil_ann.width, height=pil_ann.height)
        self.canvas.delete("all")
        self.canvas.create_image(pil_ann.width//2, pil_ann.height//2, image=self.tkimg)
        bh = len(cents_h)
        bd = len(cents_d)
        tot = bh + bd
        pct = (bd / tot * 100) if tot else 0
        self.label.config(text=f"Blue nuclei: {bh}\nBrown stained spots: {bd}\n% brown staining: {pct:.2f}%")

    def count_blobs(self):
        """
        Process the image and update the display with current parameters.
        """
        self.update_dots(None)

    def run(self):
        """
        Start the application main loop if managing the root window.
        """
        if self.manage_root:
            self.root.mainloop()


if __name__ == "__main__":
    app = DotCounterApp()
    app.run()