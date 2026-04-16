#!/usr/bin/env python3
"""
Station Map GUI - Fixed v2 - Legend editing works properly
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import os
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.image as mpimg

# ═══════════════════════════════════════════════════════════════════════════════
# LOCATION DATABASE
# ═══════════════════════════════════════════════════════════════════════════════
LOCATION_COORDS = {
    'Chamoli': (30.33, 79.33, 4.8),
    'Uttarkashi': (30.73, 78.43, 5.2),
    'Chamba': (32.73, 76.13, 4.5),
    'Pithoragarh': (29.63, 80.23, 4.3),
    'Bageshwar': (29.83, 79.53, 4.0),
    'Kangra': (31.93, 76.13, 4.4),
    'Almora': (29.63, 79.63, 3.9),
    'Bhutan': (27.50, 90.50, 4.8),
    'Nepal': (28.00, 84.00, 6.0),
    'Uttarakhand': (30.0, 79.0, 4.8),
}

INDIA_BOUNDARY = [
    (35.5, 77.0), (35.0, 78.0), (34.5, 78.5), (34.0, 79.0),
    (33.0, 79.5), (32.0, 80.0), (31.0, 80.5), (30.0, 81.0),
    (29.0, 81.5), (28.0, 82.0), (27.0, 82.5), (26.0, 83.0),
    (25.0, 83.5), (24.0, 84.0), (23.0, 84.5), (22.0, 85.0),
    (21.0, 85.5), (20.0, 86.0), (19.0, 86.5), (18.0, 87.0),
    (17.0, 87.5), (16.0, 88.0), (15.0, 88.5), (14.0, 89.0),
    (13.0, 89.5), (12.0, 90.0), (11.0, 90.5), (10.0, 91.0),
    (9.0, 92.0), (8.0, 93.0), (7.0, 94.0), (6.0, 95.0),
    (10.0, 100.0), (11.0, 101.0), (12.0, 102.0), (13.0, 103.0),
    (14.0, 104.0), (15.0, 105.0), (16.0, 106.0), (17.0, 107.0),
    (18.0, 108.0), (19.0, 109.0), (20.0, 110.0), (21.0, 110.5),
    (22.0, 111.0), (23.0, 111.5), (24.0, 112.0), (25.0, 112.5),
    (26.0, 113.0), (27.0, 113.5), (28.0, 114.0), (29.0, 114.5),
    (30.0, 115.0), (31.0, 115.5), (32.0, 116.0), (33.0, 116.5),
    (34.0, 117.0), (35.0, 117.5), (35.5, 118.0), (36.0, 117.0),
    (36.5, 116.0), (36.0, 115.0), (35.5, 114.0), (35.0, 113.0),
    (35.0, 112.0), (35.5, 111.0), (36.0, 110.0), (35.5, 109.0),
    (35.0, 108.0), (34.5, 107.0), (34.0, 106.0), (33.5, 105.0),
    (33.0, 104.0), (32.5, 103.0), (32.0, 102.0), (31.5, 101.0),
    (31.0, 100.0), (30.5, 99.0), (30.0, 98.0), (29.5, 97.0),
    (29.0, 96.0), (30.0, 95.0), (31.0, 94.0), (32.0, 93.0),
    (33.0, 92.0), (34.0, 91.0), (35.0, 90.0), (35.5, 89.0),
    (36.0, 88.0), (35.5, 87.0), (35.0, 86.0), (35.5, 85.0),
    (36.0, 84.0), (36.5, 83.0), (37.0, 82.0), (37.5, 81.0),
    (37.0, 80.0), (36.5, 79.0), (36.0, 78.0), (35.5, 77.0),
]


class LegendSettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings, update_callback):
        super().__init__(parent)
        self.title("Edit Legend & Plot Settings")
        self.geometry("450x700")
        self.configure(bg='#1E2A3A')
        
        self.settings = settings
        self.update_callback = update_callback
        self.color_vars = {}
        self._build_ui()
    
    def _build_ui(self):
        canvas = tk.Canvas(self, bg='#1E2A3A')
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg='#1E2A3A')
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        tk.Label(scrollable, text="Edit Legend & Plot Settings", bg='#1A3A5C', fg='#64B5F6',
                 font=('Helvetica',12,'bold'), pady=10).pack(fill=tk.X)
        
        # Source settings
        tk.Label(scrollable, text="Source Marker", bg='#1E2A3A', fg='#90CAF9', 
                 font=('Helvetica',10,'bold')).pack(pady=(10,5), anchor='w', padx=10)
        
        self._add_entry(scrollable, "source_marker", self.settings.get('source_marker', '*'), "Marker")
        self._add_entry(scrollable, "source_size", str(self.settings.get('source_size', 200)), "Size")
        self._add_color(scrollable, "source_color", self.settings.get('source_color', '#FF0000'), "Color")
        
        # Station settings
        tk.Label(scrollable, text="Station Marker", bg='#1E2A3A', fg='#90CAF9', 
                 font=('Helvetica',10,'bold')).pack(pady=(10,5), anchor='w', padx=10)
        
        self._add_entry(scrollable, "station_marker", self.settings.get('station_marker', 'o'), "Marker")
        self._add_entry(scrollable, "station_size", str(self.settings.get('station_size', 80)), "Size")
        self._add_color(scrollable, "station_color", self.settings.get('station_color', '#0000FF'), "Color")
        
        # Circle settings
        tk.Label(scrollable, text="Distance Circles", bg='#1E2A3A', fg='#90CAF9', 
                 font=('Helvetica',10,'bold')).pack(pady=(10,5), anchor='w', padx=10)
        
        self._add_entry(scrollable, "circle_linewidth", str(self.settings.get('circle_linewidth', 2.0)), "Line Width")
        self._add_entry(scrollable, "circle_linestyle", self.settings.get('circle_linestyle', '--'), "Line Style")
        
        for dist in [10, 50, 100, 200, 500]:
            self._add_color(scrollable, f"circle_{dist}", 
                           self.settings.get(f'circle_{dist}', '#FF0000'), 
                           f"{dist} km Color")
        
        # Boundary settings
        tk.Label(scrollable, text="Boundaries", bg='#1E2A3A', fg='#90CAF9', 
                 font=('Helvetica',10,'bold')).pack(pady=(10,5), anchor='w', padx=10)
        
        self._add_color(scrollable, "india_color", self.settings.get('india_color', '#888888'), "India Color")
        self._add_entry(scrollable, "india_linewidth", str(self.settings.get('india_linewidth', 1.5)), "India Width")
        self._add_color(scrollable, "nepal_color", self.settings.get('nepal_color', '#FF6666'), "Nepal Color")
        
        # Legend text
        tk.Label(scrollable, text="Labels", bg='#1E2A3A', fg='#90CAF9', 
                 font=('Helvetica',10,'bold')).pack(pady=(10,5), anchor='w', padx=10)
        
        self._add_entry(scrollable, "source_label", self.settings.get('source_label', 'Earthquake Source'), "Source Label")
        
        # Buttons
        btn_frame = tk.Frame(scrollable, bg='#1E2A3A')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Apply", command=self._apply,
                  bg='#27AE60', fg='white', font=('Helvetica',10,'bold'), padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Reset", command=self._reset,
                  bg='#E74C3C', fg='white', font=('Helvetica',10), padx=15).pack(side=tk.LEFT, padx=5)
    
    def _add_entry(self, parent, key, default, label):
        frame = tk.Frame(parent, bg='#1E2A3A')
        frame.pack(fill=tk.X, padx=15, pady=2)
        tk.Label(frame, text=f"{label}:", bg='#1E2A3A', fg='white', width=12, anchor='w').pack(side=tk.LEFT)
        var = tk.StringVar(value=default)
        setattr(self, f"var_{key}", var)
        tk.Entry(frame, textvariable=var, bg='#0D1B2A', fg='white', width=15).pack(side=tk.LEFT)
    
    def _add_color(self, parent, key, default, label):
        frame = tk.Frame(parent, bg='#1E2A3A')
        frame.pack(fill=tk.X, padx=15, pady=2)
        tk.Label(frame, text=f"{label}:", bg='#1E2A3A', fg='white', width=12, anchor='w').pack(side=tk.LEFT)
        
        var = tk.StringVar(value=default)
        setattr(self, f"var_{key}", var)
        
        btn = tk.Button(frame, text="Pick", bg=default, fg='white', width=8,
                       command=lambda k=key: self._pick_color(k))
        btn.pack(side=tk.LEFT, padx=5)
    
    def _pick_color(self, key):
        color = colorchooser.askcolor(title=f"Choose {key}")[1]
        if color:
            getattr(self, f"var_{key}").set(color)
            # Update button color
            for widget in self.winfo_children():
                if isinstance(widget, tk.Canvas):
                    pass
    
    def _apply(self):
        new_settings = {}
        
        # Get all entry values - convert to proper types
        entry_keys = ['source_marker', 'source_size', 'station_marker', 'station_size',
                     'circle_linewidth', 'circle_linestyle', 'india_linewidth', 'source_label']
        
        for key in entry_keys:
            var = getattr(self, f"var_{key}", None)
            if var:
                val = var.get()
                # Convert numeric values
                if key in ['source_size', 'station_size', 'circle_linewidth', 'india_linewidth']:
                    try:
                        new_settings[key] = float(val)
                    except:
                        new_settings[key] = val
                else:
                    new_settings[key] = val
        
        # Get colors
        color_keys = ['source_color', 'station_color', 'india_color', 'nepal_color']
        for key in color_keys:
            var = getattr(self, f"var_{key}", None)
            if var:
                new_settings[key] = var.get()
        
        # Circle colors
        for dist in [10, 50, 100, 200, 500]:
            var = getattr(self, f"var_circle_{dist}", None)
            if var:
                new_settings[f'circle_{dist}'] = var.get()
        
        self.update_callback(new_settings)
        self.destroy()
    
    def _reset(self):
        defaults = {
            'source_marker': '*', 'source_color': '#FF0000', 'source_size': '200',
            'station_marker': 'o', 'station_color': '#0000FF', 'station_size': '80',
            'circle_10': '#00FF00', 'circle_50': '#00FFFF', 'circle_100': '#FFFF00',
            'circle_200': '#FFA500', 'circle_500': '#FF0000',
            'circle_linewidth': '2.0', 'circle_linestyle': '--',
            'india_color': '#888888', 'india_linewidth': '1.5',
            'nepal_color': '#FF6666', 'source_label': 'Earthquake Source'
        }
        
        for key, val in defaults.items():
            var = getattr(self, f"var_{key}", None)
            if var:
                var.set(str(val))


class StationMapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Earthquake Station Map - Fixed v2")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2C3E50')
        
        self.earthquake_data = []
        self.background_image = None
        
        # Default settings - stored as proper types
        self.settings = {
            'source_marker': '*', 'source_color': '#FF0000', 'source_size': 200,
            'station_marker': 'o', 'station_color': '#0000FF', 'station_size': 80,
            'circle_10': '#00FF00', 'circle_50': '#00FFFF', 'circle_100': '#FFFF00',
            'circle_200': '#FFA500', 'circle_500': '#FF0000',
            'circle_linewidth': 2.0, 'circle_linestyle': '--',
            'india_color': '#888888', 'india_linewidth': 1.5,
            'nepal_color': '#FF6666', 'nepal_linewidth': 2.0,
            'source_label': 'Earthquake Source',
            'show_labels': True, 'show_legend': True
        }
        
        self._build_ui()
    
    def _build_ui(self):
        header = tk.Frame(self.root, bg='#1A3A5C', height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text="Station Map - Fixed Legend Editor",
                 bg='#1A3A5C', fg='#64B5F6', font=('Helvetica',12,'bold')).pack(pady=10)
        
        main = tk.Frame(self.root, bg='#2C3E50')
        main.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        left = tk.Frame(main, bg='#1E2A3A', width=280)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,4))
        left.pack_propagate(False)
        
        tk.Button(left, text="📁 Load Data Folder", command=self._load_data,
                  bg='#27AE60', fg='white', font=('Helvetica',10,'bold'), padx=10, pady=6).pack(fill=tk.X, padx=8, pady=6)
        
        tk.Button(left, text="🖼️ Load Background Image", command=self._load_background_image,
                  bg='#3498DB', fg='white', font=('Helvetica',9), padx=10, pady=4).pack(fill=tk.X, padx=8, pady=4)
        
        self.bg_var = tk.BooleanVar(value=False)
        tk.Checkbutton(left, text="Show Background Image", variable=self.bg_var,
                      bg='#1E2A3A', fg='white', selectcolor='#1E2A3A',
                      command=self._update_map).pack(anchor='w', padx=20, pady=4)
        
        tk.Label(left, text="Background Transparency:", bg='#1E2A3A', fg='#90CAF9', font=('Helvetica',8)).pack(pady=(5,0))
        self.alpha_slider = tk.Scale(left, from_=0, to=100, orient=tk.HORIZONTAL,
                                      bg='#1E2A3A', fg='white', length=200,
                                      command=lambda v: self._update_map())
        self.alpha_slider.set(30)
        self.alpha_slider.pack(padx=8)
        
        tk.Label(left, text="Distance Circles (km):", bg='#1E2A3A', fg='#90CAF9').pack(pady=(10,4))
        
        self.dist_vars = {}
        for dist in [10, 50, 100, 200, 500]:
            var = tk.BooleanVar(value=True)
            self.dist_vars[dist] = var
            tk.Checkbutton(left, text=f"{dist} km", variable=var, bg='#1E2A3A', fg='white',
                          selectcolor='#1E2A3A', command=self._update_map).pack(anchor='w', padx=20)
        
        tk.Button(left, text="⚙️ Edit Legend Settings", command=self._edit_legend,
                  bg='#9B59B6', fg='white', font=('Helvetica',9), padx=10, pady=6).pack(fill=tk.X, padx=8, pady=8)
        
        self.india_var = tk.BooleanVar(value=True)
        tk.Checkbutton(left, text="India Boundary", variable=self.india_var,
                      bg='#1E2A3A', fg='white', selectcolor='#1E2A3A',
                      command=self._update_map).pack(anchor='w', padx=20)
        
        self.nepal_var = tk.BooleanVar(value=True)
        tk.Checkbutton(left, text="Nepal Border", variable=self.nepal_var,
                      bg='#1E2A3A', fg='white', selectcolor='#1E2A3A',
                      command=self._update_map).pack(anchor='w', padx=20)
        
        self.labels_var = tk.BooleanVar(value=True)
        tk.Checkbutton(left, text="Show Labels", variable=self.labels_var,
                      bg='#1E2A3A', fg='white', selectcolor='#1E2A3A',
                      command=self._update_map).pack(anchor='w', padx=20)
        
        self.legend_var = tk.BooleanVar(value=True)
        tk.Checkbutton(left, text="Show Legend", variable=self.legend_var,
                      bg='#1E2A3A', fg='white', selectcolor='#1E2A3A',
                      command=self._update_map).pack(anchor='w', padx=20)
        
        tk.Label(left, text="Source Coordinates:", bg='#1E2A3A', fg='#90CAF9').pack(pady=(10,4))
        self.source_var = tk.StringVar(value='')
        tk.Entry(left, textvariable=self.source_var, bg='#0D1B2A', fg='#E3F2FD', width=22).pack(padx=8, pady=2)
        tk.Button(left, text="Apply", command=self._update_map,
                  bg='#1565C0', fg='white', padx=8).pack(pady=2)
        
        tk.Label(left, text="Earthquakes:", bg='#1E2A3A', fg='#90CAF9').pack(pady=(10,4))
        
        self.eq_listbox = tk.Listbox(left, bg='#0D1B2A', fg='#E3F2FD', height=8)
        self.eq_listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.eq_listbox.bind('<<ListboxSelect>>', self._on_select)
        
        tk.Button(left, text="💾 Save Image", command=self._save_image,
                  bg='#8E44AD', fg='white', font=('Helvetica',9), padx=10, pady=6).pack(fill=tk.X, padx=8, pady=6)
        
        right = tk.Frame(main, bg='#1E2A3A')
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(12,10), facecolor='white')
        self.cv = FigureCanvasTkAgg(self.fig, master=right)
        self.cv.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        toolbar = tk.Frame(right, bg='#1E2A3A')
        toolbar.pack(fill=tk.X)
        NavigationToolbar2Tk(self.cv, toolbar)
        
        self._show_empty_map()
    
    def _load_background_image(self):
        filepath = filedialog.askopenfilename(
            title="Select Background Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.JPG *.JPEG *.PNG *.BMP"),
                ("All files", "*.*")
            ]
        )
        
        if filepath:
            try:
                self.background_image = mpimg.imread(filepath)
                messagebox.showinfo("Success", "Background image loaded!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image: {e}")
    
    def _load_data(self):
        folder = filedialog.askdirectory(title="Select Folder with Zip Files")
        if not folder:
            return
        
        zip_files = [f for f in os.listdir(folder) if f.endswith('.zip')]
        
        if not zip_files:
            messagebox.showwarning("No Data", "No zip files found")
            return
        
        self.earthquake_data = []
        
        for zip_file in sorted(zip_files):
            name = zip_file.replace('.zip', '')
            lat, lon, mag = self._get_coords(name)
            self.earthquake_data.append({
                'name': name, 'zip_file': zip_file, 'lat': lat, 'lon': lon, 'magnitude': mag
            })
        
        self.eq_listbox.delete(0, tk.END)
        for eq in self.earthquake_data:
            self.eq_listbox.insert(tk.END, f"{eq['name']} (M{eq['magnitude']})")
        
        if self.earthquake_data:
            self.eq_listbox.selection_set(0)
            self._on_select(None)
    
    def _get_coords(self, name):
        for loc, (lat, lon, mag) in LOCATION_COORDS.items():
            if loc.lower() in name.lower():
                return lat, lon, mag
        return 30.0, 79.0, 4.5
    
    def _on_select(self, event):
        selection = self.eq_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        eq = self.earthquake_data[idx]
        self.source_var.set(f"{eq['lat']:.2f}, {eq['lon']:.2f}")
        self._update_map()
    
    def _show_empty_map(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Load data and select earthquake\nto view station map',
                ha='center', va='center', transform=ax.transAxes, fontsize=14, color='gray')
        self.cv.draw()
    
    def _edit_legend(self):
        dialog = LegendSettingsDialog(self.root, self.settings, self._update_settings)
    
    def _update_settings(self, new_settings):
        # Convert string values to proper types
        for key, val in new_settings.items():
            if key in ['source_size', 'station_size', 'circle_linewidth', 'india_linewidth']:
                try:
                    self.settings[key] = float(val)
                except:
                    self.settings[key] = val
            else:
                self.settings[key] = val
        self._update_map()
    
    def _update_map(self):
        if not self.earthquake_data:
            self._show_empty_map()
            return
        
        selection = self.eq_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        eq = self.earthquake_data[idx]
        
        src_lat = eq['lat']
        src_lon = eq['lon']
        
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        # Background
        if self.bg_var.get() and self.background_image is not None:
            alpha = self.alpha_slider.get() / 100.0
            ax.imshow(self.background_image, extent=[src_lon-5, src_lon+5, src_lat-5, src_lat+5], 
                     alpha=alpha, aspect='auto', zorder=0)
        
        # India
        if self.india_var.get():
            lats = [p[0] for p in INDIA_BOUNDARY]
            lons = [p[1] for p in INDIA_BOUNDARY]
            ax.plot(lons, lats, '-', color=self.settings['india_color'], 
                   linewidth=self.settings['india_linewidth'], alpha=0.6, label='India')
        
        # Nepal
        if self.nepal_var.get():
            nepal_lats = [26.4, 27.0, 28.0, 28.5, 29.0, 29.5, 30.0, 30.5, 30.0, 29.5, 28.5, 27.5, 26.4]
            nepal_lons = [80.5, 80.5, 81.0, 82.0, 83.0, 84.0, 84.5, 84.0, 83.0, 82.0, 81.0, 80.5, 80.5]
            ax.plot(nepal_lons, nepal_lats, '--', color=self.settings['nepal_color'], 
                   linewidth=2, alpha=0.8, label='Nepal')
        
        # Source - ensure numeric values
        src_size = int(self.settings.get('source_size', 200))
        st_size = int(self.settings.get('station_size', 80))
        
        ax.plot(src_lon, src_lat, self.settings['source_marker'], 
                markersize=src_size//20, 
                color=self.settings['source_color'], 
                markeredgecolor='black', label=self.settings['source_label'])
        
        if self.labels_var.get():
            ax.annotate(f"{eq['name']}\nM{eq['magnitude']}", (src_lon, src_lat), 
                       textcoords="offset points", xytext=(15,10),
                       fontsize=10, fontweight='bold', color='red',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Circles
        lat_per_km = 1 / 111.0
        lon_per_km = 1 / (111.0 * np.cos(np.radians(src_lat)))
        
        for dist, var in self.dist_vars.items():
            if var.get():
                r_lat = dist * lat_per_km
                r_lon = dist * lon_per_km
                
                theta = np.linspace(0, 2*np.pi, 100)
                circle_lat = src_lat + r_lat * np.sin(theta)
                circle_lon = src_lon + r_lon * np.cos(theta)
                
                color = self.settings.get(f'circle_{dist}', '#FF0000')
                ls = self.settings.get('circle_linestyle', '--')
                lw = self.settings.get('circle_linewidth', 2.0)
                
                ax.plot(circle_lon, circle_lat, ls, color=color, 
                       linewidth=lw, alpha=0.8, label=f'{dist} km')
                
                if self.labels_var.get():
                    label_lat = src_lat + r_lat * 0.7
                    label_lon = src_lon + r_lon * 0.7
                    ax.annotate(f'{dist}km', (label_lon, label_lat), fontsize=8, color=color, alpha=0.8)
        
        # Stations
        stations = self._get_station_locations(eq['name'])
        for st_name, (st_lat, st_lon) in stations.items():
            dist = self._calculate_distance(src_lat, src_lon, st_lat, st_lon)
            ax.plot(st_lon, st_lat, self.settings['station_marker'], 
                   markersize=st_size//20, 
                   color=self.settings['station_color'],
                   markeredgecolor='white', markeredgewidth=1)
            
            if self.labels_var.get():
                ax.annotate(f"{st_name}\n({dist:.0f}km)", (st_lon, st_lat),
                           textcoords="offset points", xytext=(5,5), fontsize=7,
                           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # Reference cities
        ref_locations = {'Delhi': (28.61, 77.21), 'Dehradun': (30.32, 78.03), 'Haridwar': (29.96, 78.16)}
        for name, (lat, lon) in ref_locations.items():
            if self.labels_var.get():
                ax.plot(lon, lat, 's', markersize=8, color='purple', alpha=0.6)
                ax.annotate(name, (lon, lat), textcoords="offset points", xytext=(3,3), fontsize=8, color='purple')
        
        ax.set_xlabel('Longitude (°E)', fontsize=10)
        ax.set_ylabel('Latitude (°N)', fontsize=10)
        ax.set_title(f"Station Map - {eq['name']} (M{eq['magnitude']})\nSource: {src_lat:.2f}°N, {src_lon:.2f}°E",
                    fontsize=14, fontweight='bold')
        
        if self.legend_var.get():
            ax.legend(loc='lower left', fontsize=8, framealpha=0.9)
        
        ax.grid(True, alpha=0.3)
        
        margin = 3.0
        ax.set_xlim(src_lon - margin, src_lon + margin)
        ax.set_ylim(src_lat - margin, src_lat + margin)
        ax.set_aspect('equal')
        
        self.fig.tight_layout()
        self.cv.draw()
    
    def _get_station_locations(self, eq_name):
        return {
            'BAG': (29.85, 79.87), 'CHM': (30.33, 79.33), 'DPR': (29.44, 79.44),
            'HAL': (29.95, 79.53), 'KGR': (30.21, 78.78), 'LHW': (30.45, 78.12),
            'RNK': (29.62, 79.41),
        }
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        R = 6371
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c
    
    def _save_image(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG", "*.png"), ("PDF", "*.pdf")])
        if filepath:
            self.fig.savefig(filepath, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Saved", f"Image saved to {filepath}")


if __name__ == "__main__":
    root = tk.Tk()
    app = StationMapApp(root)
    root.mainloop()