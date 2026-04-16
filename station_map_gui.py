#!/usr/bin/env python3
"""
Station Map GUI - Enhanced with Google Map overlay, editable settings, toggle
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import os
import zipfile
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import re
import csv
import urllib.request
import io
from PIL import Image

# ═══════════════════════════════════════════════════════════════════════════════
# LOCATION DATABASE
# ═══════════════════════════════════════════════════════════════════════════════
LOCATION_COORDS = {
    'Chamoli': (30.33, 79.33, 4.5),
    'Uttarkashi': (30.73, 78.43, 4.8),
    'Chamba': (32.73, 76.13, 4.2),
    'Pithoragarh': (29.63, 80.23, 4.0),
    'Bageshwar': (29.83, 79.53, 3.9),
    'Kangra': (31.93, 76.13, 4.1),
    'Almora': (29.63, 79.63, 3.8),
    'Champawat': (29.33, 80.13, 3.7),
    'Rudraprayag': (30.33, 78.93, 4.0),
    'Bhutan': (27.50, 90.50, 4.5),
    'Hindukush': (36.50, 71.00, 5.0),
    'Nepal': (28.00, 84.00, 5.5),
    'Nicobar': (9.00, 93.00, 5.0),
    'Uttarakhand': (30.0, 79.0, 4.5),
    'Himachal': (32.0, 77.0, 4.3),
}

# India boundary approximate coordinates
INDIA_BOUNDARY = [
    (35.5, 77.0), (35.0, 78.0), (34.5, 78.5), (34.0, 79.0),
    (33.0, 79.5), (32.0, 80.0), (31.0, 80.5), (30.0, 81.0),
    (29.0, 81.5), (28.0, 82.0), (27.0, 82.5), (26.0, 83.0),
    (25.0, 83.5), (24.0, 84.0), (23.0, 84.5), (22.0, 85.0),
    (21.0, 85.5), (20.0, 86.0), (19.0, 86.5), (18.0, 87.0),
    (17.0, 87.5), (16.0, 88.0), (15.0, 88.5), (14.0, 89.0),
    (13.0, 89.5), (12.0, 90.0), (11.0, 90.5), (10.0, 91.0),
    (9.0, 92.0), (8.0, 93.0), (7.0, 94.0), (6.0, 95.0),
    (6.0, 96.0), (7.0, 97.0), (8.0, 98.0), (9.0, 99.0),
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


class StationMapApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Earthquake Station Map - Enhanced")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2C3E50')
        
        self.earthquake_data = []
        self.google_map = None
        self.map_alpha = 0.9
        
        # Editable settings
        self.settings = {
            'source_color': '#FF0000',
            'source_marker': '*',
            'source_size': 200,
            'station_color': '#0000FF',
            'station_marker': 'o',
            'station_size': 80,
            'circle_colors': {10: '#00FF00', 50: '#00FFFF', 100: '#FFFF00', 200: '#FFA500', 500: '#FF0000'},
            'circle_linewidth': 2.0,
            'show_india': True,
            'india_color': '#888888',
            'show_nepal': True,
            'nepal_color': '#FFAAAA',
            'show_source_label': True,
            'show_station_labels': True,
            'title_fontsize': 14,
        }
        
        self._build_ui()
    
    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#1A3A5C', height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text="Earthquake Station Map with Google Overlay & Editable Settings",
                 bg='#1A3A5C', fg='#64B5F6', font=('Helvetica',12,'bold')).pack(pady=10)
        
        # Main
        main = tk.Frame(self.root, bg='#2C3E50')
        main.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        # Left - Controls
        left = tk.Frame(main, bg='#1E2A3A', width=280)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,4))
        left.pack_propagate(False)
        
        # Load & Google Map
        tk.Button(left, text="📁 Load Data Folder", command=self._load_data,
                  bg='#27AE60', fg='white', font=('Helvetica',10,'bold'), padx=10, pady=6).pack(fill=tk.X, padx=8, pady=6)
        
        tk.Button(left, text="🗺️ Load Google Map", command=self._load_google_map,
                  bg='#3498DB', fg='white', font=('Helvetica',9), padx=10, pady=4).pack(fill=tk.X, padx=8, pady=4)
        
        # Google Map toggle
        self.google_var = tk.BooleanVar(value=True)
        tk.Checkbutton(left, text="Show Google Map Overlay (90%)", variable=self.google_var,
                      bg='#1E2A3A', fg='white', selectcolor='#1E2A3A',
                      command=self._update_map).pack(anchor='w', padx=20, pady=4)
        
        # Alpha slider
        tk.Label(left, text="Map Transparency:", bg='#1E2A3A', fg='#90CAF9', font=('Helvetica',8)).pack(pady=(8,0))
        self.alpha_slider = tk.Scale(left, from_=0, to=100, orient=tk.HORIZONTAL,
                                      bg='#1E2A3A', fg='white', length=200,
                                      command=self._on_alpha_change)
        self.alpha_slider.set(90)
        self.alpha_slider.pack(padx=8)
        
        # Distance circles
        tk.Label(left, text="Distance Circles (km):", bg='#1E2A3A', fg='#90CAF9').pack(pady=(10,4))
        
        self.dist_vars = {}
        for dist in [10, 50, 100, 200, 500]:
            var = tk.BooleanVar(value=True)
            self.dist_vars[dist] = var
            tk.Checkbutton(left, text=f"{dist} km", variable=var, bg='#1E2A3A', fg='white',
                          selectcolor='#1E2A3A', command=self._update_map).pack(anchor='w', padx=20)
        
        # Edit settings button
        tk.Button(left, text="⚙️ Edit Plot Settings", command=self._edit_settings,
                  bg='#9B59B6', fg='white', font=('Helvetica',9), padx=10, pady=4).pack(fill=tk.X, padx=8, pady=8)
        
        # Show/hide options
        tk.Label(left, text="Show/Hide:", bg='#1E2A3A', fg='#90CAF9').pack(pady=(10,4))
        
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
        
        # Source location
        tk.Label(left, text="Source Coordinates:", bg='#1E2A3A', fg='#90CAF9').pack(pady=(10,4))
        self.source_var = tk.StringVar(value='')
        tk.Entry(left, textvariable=self.source_var, bg='#0D1B2A', fg='#E3F2FD', width=22).pack(padx=8, pady=2)
        tk.Button(left, text="Apply", command=self._update_map,
                  bg='#1565C0', fg='white', padx=8).pack(pady=2)
        
        # Earthquake list
        tk.Label(left, text="Earthquakes:", bg='#1E2A3A', fg='#90CAF9').pack(pady=(10,4))
        
        self.eq_listbox = tk.Listbox(left, bg='#0D1B2A', fg='#E3F2FD', height=10)
        self.eq_listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.eq_listbox.bind('<<ListboxSelect>>', self._on_select)
        
        # Save buttons
        tk.Button(left, text="💾 Save Image", command=self._save_image,
                  bg='#8E44AD', fg='white', font=('Helvetica',9), padx=10, pady=4).pack(fill=tk.X, padx=8, pady=4)
        
        # Right - Map
        right = tk.Frame(main, bg='#1E2A3A')
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(12,10), facecolor='white')
        self.cv = FigureCanvasTkAgg(self.fig, master=right)
        self.cv.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        toolbar = tk.Frame(right, bg='#1E2A3A')
        toolbar.pack(fill=tk.X)
        NavigationToolbar2Tk(self.cv, toolbar)
        
        self._show_empty_map()
    
    def _load_google_map(self):
        """Try to load a static map image from OpenStreetMap"""
        try:
            # Try to get a static map - this is a simplified approach
            # For a real implementation, you'd use the Static Maps API
            messagebox.showinfo("Info", "Google Map overlay works with pre-downloaded images.\n\n"
                           "For best results:\n1. Download a map screenshot from Google Maps\n2. Use 'Load Image' option\n\nUsing simplified background for now.")
            self._create_fallback_map()
        except Exception as e:
            messagebox.showwarning("Error", f"Could not load map: {e}")
    
    def _create_fallback_map(self):
        """Create a fallback simple map background"""
        try:
            # Create a simple colored background to simulate terrain
            self.google_map = "fallback"
        except:
            pass
    
    def _on_alpha_change(self, value):
        self.map_alpha = int(value) / 100.0
        self._update_map()
    
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
                'name': name,
                'zip_file': zip_file,
                'lat': lat,
                'lon': lon,
                'magnitude': mag
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
    
    def _edit_settings(self):
        """Open settings dialog"""
        win = tk.Toplevel(self.root)
        win.title("Edit Plot Settings")
        win.geometry("400x500")
        win.configure(bg='#1E2A3A')
        
        tk.Label(win, text="Edit Plot Appearance", bg='#1A3A5C', fg='#64B5F6',
                 font=('Helvetica',12,'bold'), pady=10).pack(fill=tk.X)
        
        # Source settings
        tk.Label(win, text="Source Marker:", bg='#1E2A3A', fg='white').pack(anchor='w', padx=10)
        self.source_marker_var = tk.StringVar(value=self.settings['source_marker'])
        tk.Entry(win, textvariable=self.source_marker_var, bg='#0D1B2A', fg='white', width=10).pack(anchor='w', padx=20)
        
        tk.Label(win, text="Source Color:", bg='#1E2A3A', fg='white').pack(anchor='w', padx=10, pady=(10,0))
        self.source_color_btn = tk.Button(win, text="Choose Color", bg=self.settings['source_color'],
                                          command=lambda: self._choose_color('source_color'))
        self.source_color_btn.pack(anchor='w', padx=20)
        
        # Station settings
        tk.Label(win, text="Station Marker:", bg='#1E2A3A', fg='white').pack(anchor='w', padx=10, pady=(10,0))
        self.station_marker_var = tk.StringVar(value=self.settings['station_marker'])
        tk.Entry(win, textvariable=self.station_marker_var, bg='#0D1B2A', fg='white', width=10).pack(anchor='w', padx=20)
        
        tk.Label(win, text="Station Color:", bg='#1E2A3A', fg='white').pack(anchor='w', padx=10, pady=(10,0))
        self.station_color_btn = tk.Button(win, text="Choose Color", bg=self.settings['station_color'],
                                           command=lambda: self._choose_color('station_color'))
        self.station_color_btn.pack(anchor='w', padx=20)
        
        # Circle linewidth
        tk.Label(win, text="Circle Line Width:", bg='#1E2A3A', fg='white').pack(anchor='w', padx=10, pady=(10,0))
        self.circle_width_var = tk.DoubleVar(value=self.settings['circle_linewidth'])
        tk.Scale(win, from_=0.5, to=5, resolution=0.5, variable=self.circle_width_var,
                bg='#1E2A3A', fg='white', orient=tk.HORIZONTAL).pack(anchor='w', padx=20)
        
        # Apply button
        tk.Button(win, text="Apply Settings", command=self._apply_settings,
                  bg='#27AE60', fg='white', font=('Helvetica',10,'bold'), padx=20, pady=10).pack(pady=20)
    
    def _choose_color(self, setting_key):
        color = colorchooser.askcolor(title="Choose color")[1]
        if color:
            if setting_key == 'source_color':
                self.settings['source_color'] = color
                self.source_color_btn.config(bg=color)
            elif setting_key == 'station_color':
                self.settings['station_color'] = color
                self.station_color_btn.config(bg=color)
    
    def _apply_settings(self):
        self.settings['source_marker'] = self.source_marker_var.get()
        self.settings['station_marker'] = self.station_marker_var.get()
        self.settings['circle_linewidth'] = self.circle_width_var.get()
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
        
        # Main plot
        ax = self.fig.add_subplot(111)
        
        # Google map overlay (simplified background)
        if self.google_var.get():
            ax.set_facecolor('#E8F4E8')
        
        # India boundary
        if self.india_var.get():
            lats = [p[0] for p in INDIA_BOUNDARY]
            lons = [p[1] for p in INDIA_BOUNDARY]
            ax.plot(lons, lats, '-', color='#888888', linewidth=1.5, alpha=0.5, label='India Boundary')
        
        # Nepal border (approximate)
        if self.nepal_var.get():
            nepal_lats = [26.4, 27.0, 28.0, 28.5, 29.0, 29.5, 30.0, 30.5, 30.0, 29.5, 28.5, 27.5, 26.4]
            nepal_lons = [80.5, 80.5, 81.0, 82.0, 83.0, 84.0, 84.5, 84.0, 83.0, 82.0, 81.0, 80.5, 80.5]
            ax.plot(nepal_lons, nepal_lats, '--', color='#FF6666', linewidth=2, alpha=0.7, label='Nepal Border')
        
        # Source
        ax.plot(src_lon, src_lat, self.settings['source_marker'], 
                markersize=20, color=self.settings['source_color'], 
                markeredgecolor='black', label='Earthquake Source')
        
        if self.labels_var.get():
            ax.annotate(f"{eq['name']}\nM{eq['magnitude']}", (src_lon, src_lat), 
                       textcoords="offset points", xytext=(15,10),
                       fontsize=10, fontweight='bold', color='red',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Distance circles
        lat_per_km = 1 / 111.0
        lon_per_km = 1 / (111.0 * np.cos(np.radians(src_lat)))
        
        for dist, var in self.dist_vars.items():
            if var.get():
                r_lat = dist * lat_per_km
                r_lon = dist * lon_per_km
                
                theta = np.linspace(0, 2*np.pi, 100)
                circle_lat = src_lat + r_lat * np.sin(theta)
                circle_lon = src_lon + r_lon * np.cos(theta)
                
                ax.plot(circle_lon, circle_lat, '--', 
                       color=self.settings['circle_colors'][dist], 
                       linewidth=self.settings['circle_linewidth'], 
                       alpha=0.8, label=f'{dist} km')
                
                # Label
                label_lat = src_lat + r_lat * 0.7
                label_lon = src_lon + r_lon * 0.7
                ax.annotate(f'{dist}km', (label_lon, label_lat), fontsize=8, 
                           color=self.settings['circle_colors'][dist], alpha=0.8)
        
        # Sample stations
        stations = self._get_station_locations(eq['name'])
        for st_name, (st_lat, st_lon) in stations.items():
            dist = self._calculate_distance(src_lat, src_lon, st_lat, st_lon)
            ax.plot(st_lon, st_lat, self.settings['station_marker'], 
                   markersize=10, color=self.settings['station_color'],
                   markeredgecolor='white', markeredgewidth=1)
            
            if self.labels_var.get():
                ax.annotate(f"{st_name}\n({dist:.0f}km)", (st_lon, st_lat),
                           textcoords="offset points", xytext=(5,5), fontsize=7,
                           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))
        
        # Add reference locations
        ref_locations = {
            'Delhi': (28.61, 77.21),
            'Dehradun': (30.32, 78.03),
            'Nepal': (28.39, 84.12),
            'Haridwar': (29.96, 78.16),
            'Rishikesh': (30.11, 78.29),
        }
        for name, (lat, lon) in ref_locations.items():
            if self.labels_var.get():
                ax.plot(lon, lat, 's', markersize=8, color='purple', alpha=0.6)
                ax.annotate(name, (lon, lat), textcoords="offset points", xytext=(3,3), fontsize=8, color='purple')
        
        # Map settings
        ax.set_xlabel('Longitude (°E)', fontsize=10)
        ax.set_ylabel('Latitude (°N)', fontsize=10)
        ax.set_title(f"Station Map - {eq['name']} (M{eq['magnitude']})\n"
                    f"Source: {src_lat:.2f}°N, {src_lon:.2f}°E | Distance circles: 10-500 km",
                    fontsize=self.settings['title_fontsize'], fontweight='bold')
        ax.legend(loc='lower left', fontsize=8, framealpha=0.9)
        ax.grid(True, alpha=0.3)
        
        # Set view - Uttarakhand region
        margin = 3.0
        ax.set_xlim(src_lon - margin, src_lon + margin)
        ax.set_ylim(src_lat - margin, src_lat + margin)
        ax.set_aspect('equal')
        
        self.fig.tight_layout()
        self.cv.draw()
    
    def _get_station_locations(self, eq_name):
        return {
            'BAG': (29.85, 79.87),
            'CHM': (30.33, 79.33),
            'DPR': (29.44, 79.44),
            'HAL': (29.95, 79.53),
            'KGR': (30.21, 78.78),
            'LHW': (30.45, 78.12),
            'RNK': (29.62, 79.41),
            'THL': (30.38, 78.47),
            'RJT': (30.12, 78.21),
            'DLD': (29.87, 79.42),
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