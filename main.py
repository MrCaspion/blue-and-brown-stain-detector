import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import json
import cv2
import numpy as np
from PIL import Image, ImageTk
import pandas as pd
from skimage.color import rgb2hed
from skimage.morphology import opening, disk
from skimage.measure import label, regionprops
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from skimage.filters import threshold_otsu
from scipy import ndimage as ndi

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
        bundle_dir = os.environ['RESOURCEPATH']
        sys.path.append(bundle_dir)
        
        if os.path.exists(os.path.join(bundle_dir, 'config.py')):
            sys.path.insert(0, bundle_dir)
        elif os.path.exists(os.path.join(bundle_dir, 'python', 'config.py')):
            sys.path.insert(0, os.path.join(bundle_dir, 'python'))
    
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
                print(f"Error: Could not find config.py at {config_path}")
                sys.exit(1)
        else:
            print("Error: Could not load config.py. Make sure it's in the same directory as this script.")
            sys.exit(1)

try:
    from dotStuff import DotCounterApp
except ImportError:
    if 'RESOURCEPATH' in os.environ:
        resource_path = os.environ['RESOURCEPATH']
        dotStuff_path = os.path.join(resource_path, 'dotStuff.py')
        
        if os.path.exists(dotStuff_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location("dotStuff", dotStuff_path)
            dotStuff = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(dotStuff)
            DotCounterApp = dotStuff.DotCounterApp
        else:
            print(f"Error: Could not find dotStuff.py at {dotStuff_path}")
            sys.exit(1)
    else:
        print("Error: Could not load dotStuff.py. Make sure it's in the same directory as this script.")
        sys.exit(1)

class MainApp:
    """
    Main application class that serves as the entry point for the Image Analysis Tool.
    Provides a simple interface with options to open the parameter editor or bulk processor.
    """
    
    def __init__(self, root):
        """
        Initialize the main application window.
        
        Parameters:
            root (tk.Tk): The root Tkinter window
        """
        self.root = root
        self.root.title("Image Analysis Tool")
        self.root.geometry("500x300")
        
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(main_frame, text="Image Process", font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        desc_label = ttk.Label(main_frame, text="Choose one option", font=("Arial", 12))
        desc_label.pack(pady=10)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        params_btn = ttk.Button(button_frame, text="Change Parameters", 
                               command=self.open_parameter_editor, width=25)
        params_btn.pack(pady=10)
        
        bulk_btn = ttk.Button(button_frame, text="Bulk Process Files", 
                             command=self.open_bulk_processor, width=25)
        bulk_btn.pack(pady=10)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def open_parameter_editor(self):
        """
        Open the parameter editor window for adjusting processing parameters.
        Hides the main window while the parameter editor is open.
        """
        self.root.withdraw()
        param_window = tk.Toplevel(self.root)
        param_window.protocol("WM_DELETE_WINDOW", lambda: self.close_window(param_window))
        param_window.title("Parameter Editor")
        
        back_frame = ttk.Frame(param_window)
        back_frame.pack(fill=tk.X, pady=5)
        back_btn = ttk.Button(back_frame, text="← Back to Main Menu", 
                              command=lambda: self.close_window(param_window))
        back_btn.pack(side=tk.LEFT, padx=10)
        
        app = DotCounterApp(param_window)
    
    def open_bulk_processor(self):
        """
        Open the bulk processor window for processing multiple images.
        Hides the main window while the bulk processor is open.
        """
        self.root.withdraw()
        bulk_window = tk.Toplevel(self.root)
        bulk_window.protocol("WM_DELETE_WINDOW", lambda: self.close_window(bulk_window))
        bulk_window.title("Bulk Image Processor")
        
        back_frame = ttk.Frame(bulk_window)
        back_frame.pack(fill=tk.X, pady=5)
        back_btn = ttk.Button(back_frame, text="← Back to Main Menu", 
                             command=lambda: self.close_window(bulk_window))
        back_btn.pack(side=tk.LEFT, padx=10)
        
        BulkProcessorApp(bulk_window)
    
    def close_window(self, window):
        """
        Close a child window and show the main window again.
        
        Parameters:
            window (tk.Toplevel): The child window to close
        """
        window.destroy()
        self.root.deiconify()

class BulkProcessorApp:
    """
    Bulk Image Processor application for processing multiple image files.
    Provides functionality for selecting, searching, processing and exporting results.
    """
    
    def __init__(self, master):
        """
        Initialize the bulk processor application.
        
        Parameters:
            master (tk.Toplevel): The parent window
        """
        self.master = master
        self.master.geometry("1200x800")
        
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        controls_frame.pack(fill=tk.X, pady=5)
        
        selection_frame = ttk.Frame(controls_frame)
        selection_frame.pack(pady=5, fill=tk.X)
        
        ttk.Button(selection_frame, text="Select Folder", command=self.select_input_folder, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(selection_frame, text="Select Files", command=self.select_input_files, width=15).pack(side=tk.LEFT, padx=5)
        
        self.selection_label = ttk.Label(selection_frame, text="No files selected")
        self.selection_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(selection_frame, text="Process Images", command=self.process_images, width=15).pack(side=tk.LEFT, padx=15)
        ttk.Button(selection_frame, text="Export Results", command=self.export_results, width=15).pack(side=tk.LEFT, padx=5)
        
        search_frame = ttk.Frame(controls_frame)
        search_frame.pack(pady=5, fill=tk.X)
        
        ttk.Label(search_frame, text="Search by filename:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(search_frame, text="Search", command=self.search_files, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(search_frame, text="Clear Search", command=self.clear_search, width=10).pack(side=tk.LEFT, padx=5)
        
        self.search_result_label = ttk.Label(search_frame, text="")
        self.search_result_label.pack(side=tk.LEFT, padx=10)
        
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.canvas = tk.Canvas(results_frame)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.master, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.load_parameters()
        
        self.results = []
        
        self.all_image_files = []
        self.image_files = []
        
        search_entry.bind("<Return>", lambda event: self.search_files())
    
    def select_input_folder(self):
        """
        Select input folder containing image files.
        Updates the file list with all images found in the selected folder.
        """
        folder = filedialog.askdirectory()
        if folder:
            self.all_image_files = []
            self.input_type = "folder"
            
            for file in os.listdir(folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff')):
                    self.all_image_files.append(os.path.join(folder, file))
            
            self.image_files = self.all_image_files.copy()
            
            self.selection_label.config(text=f"Selected folder: {os.path.basename(folder)} ({len(self.image_files)} images)")
            self.status_var.set(f"Selected folder with {len(self.image_files)} image(s)")
            
            self.search_var.set("")
            self.search_result_label.config(text="")
    
    def select_input_files(self):
        """
        Select multiple individual image files.
        Updates the file list with all selected image files.
        """
        files = filedialog.askopenfilenames(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.tif *.tiff"),
                ("All files", "*.*")
            ]
        )
        if files:
            self.all_image_files = list(files)
            self.image_files = self.all_image_files.copy()
            
            self.input_type = "files"
            
            self.selection_label.config(text=f"Selected {len(self.image_files)} individual file(s)")
            self.status_var.set(f"Selected {len(self.image_files)} image file(s)")
            
            self.search_var.set("")
            self.search_result_label.config(text="")
    
    def search_files(self):
        """
        Filter image files based on search term.
        Updates the file list to show only files that match the search criteria.
        """
        if not self.all_image_files:
            self.status_var.set("No files to search. Please select files or a folder first.")
            return
        
        search_term = self.search_var.get().lower()
        if not search_term:
            self.image_files = self.all_image_files.copy()
            self.search_result_label.config(text="Showing all files")
        else:
            self.image_files = [f for f in self.all_image_files if search_term in os.path.basename(f).lower()]
            self.search_result_label.config(text=f"Found {len(self.image_files)} matching file(s)")
        
        if hasattr(self, 'input_type') and self.input_type == "folder":
            self.selection_label.config(text=f"Selected folder: {os.path.basename(os.path.dirname(self.all_image_files[0]))} ({len(self.image_files)} of {len(self.all_image_files)} images shown)")
        else:
            self.selection_label.config(text=f"Selected {len(self.image_files)} of {len(self.all_image_files)} file(s)")
        
        self.status_var.set(f"Search results: {len(self.image_files)} file(s) matching '{search_term}'")
    
    def clear_search(self):
        """
        Clear search and show all files.
        Resets the file list to show all selected files.
        """
        self.search_var.set("")
        self.image_files = self.all_image_files.copy()
        self.search_result_label.config(text="Showing all files")
        
        if hasattr(self, 'input_type') and self.input_type == "folder":
            if self.all_image_files:
                self.selection_label.config(text=f"Selected folder: {os.path.basename(os.path.dirname(self.all_image_files[0]))} ({len(self.image_files)} images)")
        else:
            self.selection_label.config(text=f"Selected {len(self.image_files)} file(s)")
        
        self.status_var.set(f"Search cleared. Showing all {len(self.image_files)} image(s).")
    
    def load_parameters(self):
        """
        Load processing parameters from the default file.
        Falls back to default constants if the parameter file is not found or is invalid.
        """
        self.params = {}
        if os.path.exists(DEFAULT_PARAMS_FILE):
            try:
                with open(DEFAULT_PARAMS_FILE, 'r') as f:
                    self.params = json.load(f)
                self.status_var.set(f"Parameters loaded from {DEFAULT_PARAMS_FILE}")
            except Exception as e:
                self.status_var.set(f"Error loading parameters: {str(e)}")
                self.params = {
                    'disk_size': DISK_SIZE,
                    'gaussian_sigma': GAUSSIAN_SIGMA,
                    'min_distance': MIN_DISTANCE,
                    'min_area_h': MIN_AREA_H,
                    'min_area_d': MIN_AREA_D,
                    'marker_radius': MARKER_RADIUS
                }
        else:
            self.status_var.set("Using default parameters (no saved parameters found)")
            self.params = {
                'disk_size': DISK_SIZE,
                'gaussian_sigma': GAUSSIAN_SIGMA,
                'min_distance': MIN_DISTANCE,
                'min_area_h': MIN_AREA_H,
                'min_area_d': MIN_AREA_D,
                'marker_radius': MARKER_RADIUS
            }
        
        params_str = ', '.join([f"{k}: {v}" for k, v in self.params.items() 
                              if k not in ['image_path', 'h_threshold', 'd_threshold']])
        self.status_var.set(f"Using parameters: {params_str}")
    
    def process_image(self, image_path):
        """
        Process a single image and return the results.
        
        Parameters:
            image_path (str): Path to the image file
            
        Returns:
            dict: Dictionary containing processing results or None if processing failed
        """
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        pil_img = Image.open(image_path)
        pil_img.thumbnail((300, 300))
        
        disk_size = int(self.params.get('disk_size', DISK_SIZE))
        gaussian_sigma = float(self.params.get('gaussian_sigma', GAUSSIAN_SIGMA))
        min_distance = int(self.params.get('min_distance', MIN_DISTANCE))
        min_area_h = int(self.params.get('min_area_h', MIN_AREA_H))
        min_area_d = int(self.params.get('min_area_d', MIN_AREA_D))
        marker_radius = int(self.params.get('marker_radius', MARKER_RADIUS))
        
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float64) / 255
        hed = rgb2hed(rgb)
        h_chan = hed[:, :, 0]
        d_chan = hed[:, :, 2]
        
        if 'h_threshold' in self.params and self.params['h_threshold'] is not None:
            th_h = float(self.params['h_threshold'])
        else:
            th_h = threshold_otsu(h_chan)
            
        if 'd_threshold' in self.params and self.params['d_threshold'] is not None:
            th_d = float(self.params['d_threshold'])
        else:
            th_d = threshold_otsu(d_chan)
        
        mask_h = opening(h_chan > th_h, disk(disk_size))
        mask_d = opening(d_chan > th_d, disk(disk_size))
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
        
        disp = np.array(pil_img)
        disp_bgr = cv2.cvtColor(disp, cv2.COLOR_RGB2BGR)
        h, w = disp.shape[:2]
        img_h, img_w = img.shape[:2]
        sx, sy = w / img_w, h / img_h
        
        for y, x in cents_h:
            dx, dy = int(x * sx), int(y * sy)
            cv2.circle(disp_bgr, (dx, dy), marker_radius, (255, 0, 0), -1)
        for y, x in cents_d:
            dx, dy = int(x * sx), int(y * sy)
            cv2.circle(disp_bgr, (dx, dy), marker_radius, (0, 0, 255), -1)
        
        ann = cv2.cvtColor(disp_bgr, cv2.COLOR_BGR2RGB)
        pil_ann = Image.fromarray(ann)
        
        num_blue = len(cents_h)
        num_red = len(cents_d)
        total = num_blue + num_red
        pct_red_of_total = (num_red / total * 100) if total > 0 else 0
        red_to_blue_ratio = (num_red / num_blue) if num_blue > 0 else float('inf')
        pct_blue_of_total = (num_blue / total * 100) if total > 0 else 0
        red_as_pct_of_blue = (num_red / num_blue * 100) if num_blue > 0 else float('inf')
        
        return {
            'filename': os.path.basename(image_path),
            'orig_img': pil_img,
            'ann_img': pil_ann,
            'blue_count': num_blue,
            'red_count': num_red,
            'total_count': total,
            'pct_red_of_total': pct_red_of_total,
            'red_blue_ratio': red_to_blue_ratio,
            'pct_blue_of_total': pct_blue_of_total,
            'red_as_pct_of_blue': red_as_pct_of_blue
        }
    
    def process_images(self):
        """
        Process all selected images.
        Updates the results display with the processing results.
        """
        if not self.image_files:
            messagebox.showerror("Error", "No images selected. Please select a folder or individual files.")
            return
        
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.results = []
        
        if not self.image_files:
            messagebox.showinfo("Info", "No image files found in the selection")
            return
        
        for i, img_path in enumerate(self.image_files):
            self.status_var.set(f"Processing image {i+1} of {len(self.image_files)}: {os.path.basename(img_path)}")
            self.master.update()
            
            result = self.process_image(img_path)
            if result:
                self.results.append(result)
                self.add_result_row(result)
        
        self.status_var.set(f"Processed {len(self.results)} images")
    
    def add_result_row(self, result):
        """
        Add a row to the results display.
        
        Parameters:
            result (dict): Processing result dictionary for a single image
        """
        row_frame = ttk.Frame(self.scrollable_frame)
        row_frame.pack(fill=tk.X, pady=10, padx=5)
        
        ttk.Label(row_frame, text=result['filename'], font=("Arial", 12, "bold")).pack(anchor="w")
        
        content_frame = ttk.Frame(row_frame)
        content_frame.pack(fill=tk.X, pady=5)
        
        orig_img_frame = ttk.LabelFrame(content_frame, text="Original")
        orig_img_frame.pack(side=tk.LEFT, padx=5)
        
        img_tk = ImageTk.PhotoImage(result['orig_img'])
        result['orig_img_tk'] = img_tk
        
        img_label = ttk.Label(orig_img_frame, image=img_tk)
        img_label.pack(padx=5, pady=5)
        
        ann_img_frame = ttk.LabelFrame(content_frame, text="Annotated")
        ann_img_frame.pack(side=tk.LEFT, padx=5)
        
        ann_img_tk = ImageTk.PhotoImage(result['ann_img'])
        result['ann_img_tk'] = ann_img_tk
        
        ann_img_label = ttk.Label(ann_img_frame, image=ann_img_tk)
        ann_img_label.pack(padx=5, pady=5)
        
        stats_frame = ttk.LabelFrame(content_frame, text="Statistics")
        stats_frame.pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        stats_text = (
            f"Blue nuclei count: {result['blue_count']}\n"
            f"Red stain count: {result['red_count']}\n"
            f"Total count: {result['total_count']}\n"
            f"Red:Blue ratio: {result['red_blue_ratio']:.2f}\n"
            f"Red as % of Blue: {result['red_as_pct_of_blue']:.2f}%\n"
            f"% Red of total: {result['pct_red_of_total']:.2f}%\n"
            f"% Blue of total: {result['pct_blue_of_total']:.2f}%"
        )
        
        ttk.Label(stats_frame, text=stats_text, justify=tk.LEFT).pack(padx=10, pady=10)
        
        ttk.Separator(self.scrollable_frame, orient='horizontal').pack(fill=tk.X, pady=5)
    
    def export_results(self):
        """
        Export results to a CSV file.
        Prompts the user for a save location and writes the results to a CSV file.
        """
        if not self.results:
            messagebox.showinfo("Info", "No results to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Results"
        )
        
        if not file_path:
            return
        
        data = []
        for result in self.results:
            data.append({
                'Filename': result['filename'],
                'Blue nuclei count': result['blue_count'],
                'Red stain count': result['red_count'],
                'Total count': result['total_count'],
                'Red:Blue ratio': result['red_blue_ratio'],
                'Red as % of Blue': result['red_as_pct_of_blue'],
                '% Red of total': result['pct_red_of_total'],
                '% Blue of total': result['pct_blue_of_total']
            })
        
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        
        self.status_var.set(f"Results exported to {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()