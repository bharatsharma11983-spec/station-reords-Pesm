#!/usr/bin/env python3
"""
Station Map GUI - FINAL VERSION v2
- Fixed trace_add() for Tcl 9
- Fixed callback arguments
- Click text to edit
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


LOCATION_COORDS = {
    'Chamoli': (30.33, 79.33, 4.8),
    'Uttarkashi': (30.73, 78.43, 5.2),
    'Bhuj': (23.23, 70.03, 6.3),
    'Kangra': (31.93, 76.13, 4.4),
    'Latur': (18.0, 76.0, 6.2),
    'Nepal': (28.0, 84.0, 6.0),
    'Uttarakhand': (30.0, 79.0, 4.8),
}

INDIA_BOUNDARY = [
    (35.5, 77.0), (35.0, 78.0), (34.5, 78.5), (34.0, 79.0),
    (33.0, 79.5), (32.0, 80.0), (31.0, 80.5), (30.0, 81.0),
    (29.0, 81.5), (28.0, 82.0), (27.0, 82.5), (26.0, 83.0),
    (25.0, 83.5), (24.0, 84.0), (23.0, 84.5), (22.0, 85.0),
    (21.0, 85.5), (20.0, 86.0), (19.0, 86.5), (18.0, 87.0),
    (17.0, 87.5), (16.0, 88.0), (15.0, 88.5), (14.0, 89.0),
    (13.0, 89.5), (12.0, 90.0), (10.0, 100.0), (15.0, 105.0),
    (20.0, 110.0), (25.0, 112.5), (30.0, 115.0), (35.0, 117.0),
    (35.5, 118.0), (36.0, 117.0), (36.5, 116.0), (36.0, 115.0),
    (35.5, 114.0), (35.0, 113.0), (35.0, 112.0), (35.5, 111.0),
    (36.0, 110.0), (35.5, 109.0), (35.0, 108.0), (35.0, 107.0),
    (35.5, 106.0), (36.0, 105.0), (36.0, 104.0), (35.5, 103.0),
    (35.0, 102.0), (35.0, 101.0), (35.5, 100.0), (36.0, 99.0),
    (35.5, 98.0), (35.0, 97.0), (35.0, 96.0), (35.5, 95.0),
    (36.0, 94.0), (35.5, 93.0), (35.0, 92.0), (35.0, 91.0),
    (35.5, 90.0), (36.0, 89.0), (36.5, 88.0), (37.0, 87.0),
    (37.5, 86.0), (37.5, 85.0), (37.0, 84.0), (36.5, 83.0),
    (36.0, 82.0), (36.0, 81.0), (35.5, 80.0), (35.5, 79.0),
    (35.5, 78.0), (35.5, 77.0),
]


class TextEditDialog(tk.Toplevel):
    def __init__(self, parent, text, fontsize, fontweight, color):
        super().__init__(parent)
        self.title("Edit Text")
        self.geometry("350x400")
        self.configure(bg='#1E2A3A')
        
        self.result = None
        self.text = text
        self.fontsize = fontsize
        self.fontweight = fontweight
        self.color = color
        
        self._build_ui()
    
    def _build_ui(self):
        f = tk.Frame(self, bg='#1E2A3A')
        f.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(f, text="Text:", bg='#1E2A3A', fg='white').pack(anchor='w')
        self.text_var = tk.StringVar(value=self.text)
        tk.Entry(f, textvariable=self.text_var, bg='#0D1B2A', fg='white', font=('Helvetica',10)).pack(fill=tk.X, pady=5)
        
        tk.Label(f, text="Font Size:", bg='#1E2A3A', fg='white').pack(anchor='w', pady=(10,0))
        self.size_var = tk.IntVar(value=self.fontsize)
        tk.Scale(f, from_=6, to=72, variable=self.size_var, orient=tk.HORIZONTAL,
                bg='#1E2A3A', fg='white').pack(fill=tk.X)
        
        tk.Label(f, text="Style:", bg='#1E2A3A', fg='white').pack(anchor='w', pady=(10,0))
        self.bold_var = tk.BooleanVar(value=(self.fontweight == 'bold'))
        tk.Checkbutton(f, text="Bold", variable=self.bold_var, bg='#1E2A3A', fg='white',
                      selectcolor='#1E2A3A').pack(anchor='w')
        
        tk.Label(f, text="Color:", bg='#1E2A3A', fg='white').pack(anchor='w', pady=(10,0))
        color_frame = tk.Frame(f, bg='#1E2A3A')
        color_frame.pack(fill=tk.X)
        
        self.color_var = tk.StringVar(value=self.color)
        self.color_btn = tk.Button(color_frame, text="Pick Color", bg=self.color, fg='white',
                            command=self._pick_color).pack(side=tk.LEFT)
        tk.Label(color_frame, textvariable=self.color_var, bg='#1E2A3A', fg='white').pack(side=tk.LEFT, padx=10)
        
        btns = tk.Frame(f, bg='#1E2A3A')
        btns.pack(pady=20)
        tk.Button(btns, text="Apply", command=self._apply, bg='#27AE60', fg='white',
                 padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="Cancel", command=self.destroy, bg='#E74C3C', fg='white',
                 padx=15).pack(side=tk.LEFT, padx=5)
    
    def _pick_color(self):
        c = colorchooser.askcolor(title="Choose Text Color")[1]
        if c:
            self.color_var.set(c)
            self.color_btn.config(bg=c)
    
    def _apply(self):
        self.result = {
            'text': self.text_var.get(),
            'fontsize': self.size_var.get(),
            'fontweight': 'bold' if self.bold_var.get() else 'normal',
            'color': self.color_var.get()
        }
        self.destroy()


class LegendSettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings, update_callback):
        super().__init__(parent)
        self.title("Edit Legend & Plot Settings")
        self.geometry("450x750")
        self.configure(bg='#1E2A3A')
        
        self.settings = settings
        self.callback = update_callback
        self.vars = {}
        
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
        
        self._add_section(scrollable, "Source Marker")
        self._add_entry(scrollable, "source_marker", "Marker:", self.settings.get('source_marker', '*'))
        self._add_entry(scrollable, "source_size", "Size:", str(int(self.settings.get('source_size', 200))))
        self._add_color_entry(scrollable, "source_color", "Color:", self.settings.get('source_color', '#FF0000'))
        
        self._add_section(scrollable, "Station Marker")
        self._add_entry(scrollable, "station_marker", "Marker:", self.settings.get('station_marker', 'o'))
        self._add_entry(scrollable, "station_size", "Size:", str(int(self.settings.get('station_size', 80))))
        self._add_color_entry(scrollable, "station_color", "Color:", self.settings.get('station_color', '#0000FF'))
        
        self._add_section(scrollable, "Distance Circles")
        self._add_entry(scrollable, "circle_linewidth", "Line Width:", str(self.settings.get('circle_linewidth', 2.0)))
        
        for dist in [10, 50, 100, 200, 500]:
            self._add_color_entry(scrollable, f"circle_{dist}", f"{dist} km:",
                           self.settings.get(f'circle_{dist}', '#FF0000'))
        
        self._add_section(scrollable, "Boundaries")
        self._add_color_entry(scrollable, "india_color", "India:", self.settings.get('india_color', '#888888'))
        self._add_entry(scrollable, "india_linewidth", "India Width:", str(self.settings.get('india_linewidth', 1.5)))
        self._add_color_entry(scrollable, "nepal_color", "Nepal:", self.settings.get('nepal_color', '#FF6666'))
        
        self._add_section(scrollable, "Labels")
        self._add_entry(scrollable, "source_label", "Source Label:", self.settings.get('source_label', 'Earthquake Source'))
        
        btns = tk.Frame(scrollable, bg='#1E2A3A')
        btns.pack(pady=15)
        tk.Button(btns, text="Apply", command=self._apply, bg='#27AE60', fg='white', padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="Reset", command=self._reset, bg='#E74C3C', fg='white', padx=15).pack(side=tk.LEFT, padx=5)
    
    def _add_section(self, parent, text):
        tk.Label(parent, text=text, bg='#1E2A3A', fg='#90CAF9',
                font=('Helvetica',10,'bold')).pack(pady=(15,5), anchor='w', padx=10)
    
    def _add_entry(self, parent, key, label, default):
        f = tk.Frame(parent, bg='#1E2A3A')
        f.pack(fill=tk.X, padx=15, pady=2)
        tk.Label(f, text=label, bg='#1E2A3A', fg='white', width=12, anchor='w').pack(side=tk.LEFT)
        self.vars[key] = tk.StringVar(value=default)
        tk.Entry(f, textvariable=self.vars[key], bg='#0D1B2A', fg='white', width=18).pack(side=tk.LEFT)
    
    def _add_color_entry(self, parent, key, label, default):
        f = tk.Frame(parent, bg='#1E2A3A')
        f.pack(fill=tk.X, padx=15, pady=2)
        tk.Label(f, text=label, bg='#1E2A3A', fg='white', width=12, anchor='w').pack(side=tk.LEFT)
        self.vars[key] = tk.StringVar(value=default)
        
        def pick(key=key):
            c = colorchooser.askcolor(title=f"Choose {key}")[1]
            if c:
                self.vars[key].set(c)
        
        tk.Button(f, text="Pick", bg=default, fg='white', width=8, command=pick).pack(side=tk.LEFT, padx=5)
    
    def _apply(self):
        new_settings = {}
        for key, var in self.vars.items():
            val = var.get()
            if key in ['source_size', 'station_size', 'circle_linewidth', 'india_linewidth']:
                try:
                    new_settings[key] = float(val)
                except:
                    new_settings[key] = val
            else:
                new_settings[key] = val
        
        self.callback(new_settings)
        self.destroy()
    
    def _reset(self):
        defaults = {
            'source_marker': '*', 'source_size': '200', 'source_color': '#FF0000',
            'station_marker': 'o', 'station_size': '80', 'station_color': '#0000FF',
            'circle_10': '#00FF00', 'circle_50': '#00FFFF', 'circle_100': '#FFFF00',
            'circle_200': '#FFA500', 'circle_500': '#FF0000', 'circle_linewidth': '2.0',
            'india_color': '#888888', 'india_linewidth': '1.5', 'nepal_color': '#FF6666',
            'source_label': 'Earthquake Source'
        }
        for key, val in defaults.items():
            self.vars[key].set(str(val))


class StationMapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Station Map GUI - FINAL v2")
        self.root.geometry("1500x1000")
        self.root.configure(bg='#2C3E50')
        
        self.earthquake_data = []
        self.background_image = None
        self.editable_texts = []
        
        self.settings = {
            'source_marker': '*', 'source_color': '#FF0000', 'source_size': 200,
            'station_marker': 'o', 'station_color': '#0000FF', 'station_size': 80,
            'circle_10': '#00FF00', 'circle_50': '#00FFFF', 'circle_100': '#FFFF00',
            'circle_200': '#FFA500', 'circle_500': '#FF0000',
            'circle_linewidth': 2.0, 'circle_linestyle': '--',
            'india_color': '#888888', 'india_linewidth': 1.5,
            'nepal_color': '#FF6666', 'source_label': 'Earthquake Source',
            'show_labels': True, 'show_legend': True
        }
        
        self._build_ui()
    
    def _build_ui(self):
        tk.Label(self.root, text="Station Map - FINAL v2 (Click text to edit)",
               bg='#1A3A5C', fg='#64B5F6', font=('Helvetica',12,'bold'), pady=10).pack(fill=tk.X)
        
        main = tk.Frame(self.root, bg='#2C3E50')
        main.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        left = tk.Frame(main, bg='#1E2A3A', width=280)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,4))
        left.pack_propagate(False)
        
        tk.Button(left, text="📁 Load Data Folder", command=self._load_data,
                  bg='#27AE60', fg='white', font=('Helvetica',10,'bold'), padx=10, pady=6).pack(fill=tk.X, padx=8, pady=6)
        
        tk.Button(left, text="🖼️ Load Background", command=self._load_bg,
                  bg='#3498DB', fg='white', padx=10, pady=4).pack(fill=tk.X, padx=8, pady=4)
        
        self.bg_var = tk.BooleanVar(value=False)
        tk.Checkbutton(left, text="Show Background", variable=self.bg_var,
                      bg='#1E2A3A', fg='white', selectcolor='#1E2A3A',
                      command=self._update_map).pack(anchor='w', padx=20, pady=4)
        
        tk.Label(left, text="Distance Circles:", bg='#1E2A3A', fg='#90CAF9').pack(pady=(10,4))
        self.dist_vars = {d: tk.BooleanVar(value=True) for d in [10, 50, 100, 200, 500]}
        for d, var in self.dist_vars.items():
            tk.Checkbutton(left, text=f"{d} km", variable=var, bg='#1E2A3A', fg='white',
                          selectcolor='#1E2A3A', command=self._update_map).pack(anchor='w', padx=20)
        
        tk.Button(left, text="⚙️ Edit Legend", command=self._edit_legend,
                  bg='#9B59B6', fg='white', padx=10, pady=6).pack(fill=tk.X, padx=8, pady=8)
        
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
        
        tk.Label(left, text="Source Coords:", bg='#1E2A3A', fg='#90CAF9').pack(pady=(10,4))
        self.source_var = tk.StringVar(value='')
        # Fixed: use trace_add instead of deprecated trace
        self.source_var.trace_add('write', self._update_map)
        tk.Entry(left, textvariable=self.source_var, bg='#0D1B2A', fg='white', width=22).pack(padx=8)
        
        tk.Label(left, text="Earthquakes:", bg='#1E2A3A', fg='#90CAF9').pack(pady=(10,4))
        self.eq_list = tk.Listbox(left, bg='#0D1B2A', fg='#E3F2FD', height=6)
        self.eq_list.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.eq_list.bind('<<ListboxSelect>>', self._on_select)
        
        tk.Button(left, text="💾 Save Image", command=self._save,
                  bg='#8E44AD', fg='white', padx=10, pady=6).pack(fill=tk.X, padx=8, pady=6)
        
        right = tk.Frame(main, bg='#1E2A3A')
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(14,10), facecolor='white')
        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.canvas.mpl_connect('button_press_event', self._on_canvas_click)
        
        toolbar = tk.Frame(right, bg='#1E2A3A')
        toolbar.pack(fill=tk.X)
        NavigationToolbar2Tk(self.canvas, toolbar)
        
        self._show_empty()
    
    def _load_bg(self):
        f = filedialog.askopenfilename(title="Select Background Image",
                                       filetypes=[("Images", "*.jpg *.png *.bmp")])
        if f:
            try:
                self.background_image = mpimg.imread(f)
                messagebox.showinfo("OK", "Background loaded!")
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def _load_data(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        
        files = [f for f in os.listdir(folder) if f.endswith('.zip')]
        if not files:
            messagebox.showwarning("Warning", "No zip files")
            return
        
        self.earthquake_data = []
        for f in sorted(files):
            name = f.replace('.zip', '')
            lat, lon, mag = self._get_coords(name)
            self.earthquake_data.append({'name': name, 'lat': lat, 'lon': lon, 'magnitude': mag})
        
        self.eq_list.delete(0, tk.END)
        for eq in self.earthquake_data:
            self.eq_list.insert(tk.END, f"{eq['name']} M{eq['magnitude']}")
        
        if self.earthquake_data:
            self.eq_list.selection_set(0)
            self._on_select(None)
    
    def _get_coords(self, name):
        for loc, (lat, lon, mag) in LOCATION_COORDS.items():
            if loc.lower() in name.lower():
                return lat, lon, mag
        return 30.0, 79.0, 4.5
    
    def _on_select(self, event):
        sel = self.eq_list.curselection()
        if not sel:
            return
        
        eq = self.earthquake_data[sel[0]]
        self.source_var.set(f"{eq['lat']:.2f}, {eq['lon']:.2f}")
        self._update_map()
    
    def _show_empty(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Load data and select earthquake',
               ha='center', va='center', transform=ax.transAxes, fontsize=14, color='gray')
        self.canvas.draw()
    
    def _edit_legend(self):
        dialog = LegendSettingsDialog(self.root, self.settings, self._update_settings)
    
    def _update_settings(self, new_settings):
        for key, val in new_settings.items():
            if key in ['source_size', 'station_size', 'circle_linewidth', 'india_linewidth']:
                try:
                    self.settings[key] = float(val)
                except:
                    self.settings[key] = val
            else:
                self.settings[key] = val
        self._update_map()
    
    def _on_canvas_click(self, event):
        if event.inaxes is None:
            return
        
        ax = event.inaxes
        for text_obj, _ in self.editable_texts:
            contains, _ = text_obj.contains(event)
            if contains:
                dialog = TextEditDialog(
                    self.root,
                    text_obj.get_text(),
                    text_obj.get_fontsize(),
                    text_obj.get_fontweight(),
                    text_obj.get_color()
                )
                self.root.wait_window(dialog)
                if dialog.result:
                    text_obj.set_text(dialog.result['text'])
                    text_obj.set_fontsize(dialog.result['fontsize'])
                    text_obj.set_fontweight(dialog.result['fontweight'])
                    text_obj.set_color(dialog.result['color'])
                    self.canvas.draw()
                return
    
    def _update_map(self, *args):
        if not self.earthquake_data:
            self._show_empty()
            return
        
        sel = self.eq_list.curselection()
        if not sel:
            return
        
        eq = self.earthquake_data[sel[0]]
        src_lat, src_lon = eq['lat'], eq['lon']
        
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self.editable_texts = []
        
        if self.bg_var.get() and self.background_image is not None:
            ax.imshow(self.background_image, extent=[src_lon-5, src_lon+5, src_lat-5, src_lat+5],
                     alpha=0.3, aspect='auto', zorder=0)
        
        if self.india_var.get():
            lats = [p[0] for p in INDIA_BOUNDARY]
            lons = [p[1] for p in INDIA_BOUNDARY]
            ax.plot(lons, lats, '-', color=self.settings['india_color'],
                   linewidth=self.settings['india_linewidth'], alpha=0.6, label='India')
        
        if self.nepal_var.get():
            nepal_lats = [26.4, 27.0, 28.0, 28.5, 29.0, 29.5, 30.0, 30.5, 30.0, 29.5, 28.5, 27.5, 26.4]
            nepal_lons = [80.5, 80.5, 81.0, 82.0, 83.0, 84.0, 84.5, 84.0, 83.0, 82.0, 81.0, 80.5, 80.5]
            ax.plot(nepal_lons, nepal_lats, '--', color=self.settings['nepal_color'],
                   linewidth=2, alpha=0.8, label='Nepal')
        
        src_size = int(self.settings.get('source_size', 200))
        ax.plot(src_lon, src_lat, self.settings['source_marker'],
               markersize=src_size//20,
               color=self.settings['source_color'],
               markeredgecolor='black',
               label=self.settings['source_label'])
        
        if self.labels_var.get():
            text = ax.annotate(f"{eq['name']}\nM{eq['magnitude']}", (src_lon, src_lat),
                             textcoords="offset points", xytext=(15,10),
                             fontsize=10, fontweight='bold', color='red',
                             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            self.editable_texts.append((text, ('source', eq)))
        
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
                ax.plot(circle_lon, circle_lat, '--', color=color,
                       linewidth=self.settings.get('circle_linewidth', 2.0),
                       alpha=0.8, label=f'{dist} km')
                
                if self.labels_var.get():
                    text = ax.annotate(f'{dist}km', (src_lon + r_lon*0.7, src_lat + r_lat*0.7),
                                      fontsize=8, color=color, alpha=0.8)
                    self.editable_texts.append((text, (f'circle_{dist}', eq)))
        
        for city, (lat, lon) in [('Delhi', (28.61, 77.21)), ('Dehradun', (30.32, 78.03))]:
            if self.labels_var.get():
                text = ax.plot(lon, lat, 's', markersize=8, color='purple', alpha=0.6)
                text = ax.annotate(city, (lon, lat), textcoords="offset points",
                                  xytext=(3,3), fontsize=8, color='purple')
                self.editable_texts.append((text, (city, eq)))
        
        ax.set_xlabel('Longitude (°E)')
        ax.set_ylabel('Latitude (°N)')
        ax.set_title(f"Station Map - {eq['name']} (M{eq['magnitude']})",
                    fontsize=14, fontweight='bold')
        
        if self.legend_var.get():
            ax.legend(loc='lower left', fontsize=8, framealpha=0.9)
        
        ax.grid(True, alpha=0.3)
        
        margin = 3.0
        ax.set_xlim(src_lon - margin, src_lon + margin)
        ax.set_ylim(src_lat - margin, src_lat + margin)
        ax.set_aspect('equal')
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def _save(self):
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG", "*.png")])
        if path:
            self.fig.savefig(path, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Saved", f"Image saved to {path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = StationMapApp(root)
    root.mainloop()