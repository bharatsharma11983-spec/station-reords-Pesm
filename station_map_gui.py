#!/usr/bin/env python3
"""
Station Data Map - Add map showing station locations and distance circles
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
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

# Map coordinates for common Indian earthquake locations
LOCATION_COORDS = {
    'Chamoli': (30.3, 79.3),
    'Uttarkashi': (30.7, 78.4),
    'Chamba': (32.7, 76.1),
    'Pithoragarh': (29.6, 80.2),
    'Bageshwar': (29.8, 79.5),
    'Kangra': (31.9, 76.1),
    'Almora': (29.6, 79.6),
    'Champawat': (29.3, 80.1),
    'Rudraprayag': (30.3, 78.9),
    'Bhutan': (27.5, 90.5),
    'Hindukush': (36.5, 71.0),
    'Nepal': (28.0, 84.0),
    'Nicobar': (9.0, 93.0),
}

class StationMapApp:
    """Map GUI for earthquake station locations"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Earthquake Station Map Viewer")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2C3E50')
        
        self.earthquake_data = []
        
        self._build_ui()
    
    def _build_ui(self):
        """Build UI"""
        # Header
        header = tk.Frame(self.root, bg='#1A3A5C', height=50)
        header.pack(fill=tk.X)
        tk.Label(header, text="Earthquake Station Map with Distance Circles",
                 bg='#1A3A5C', fg='#64B5F6', font=('Helvetica',12,'bold')).pack(pady=10)
        
        # Main
        main = tk.Frame(self.root, bg='#2C3E50')
        main.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        # Left - controls
        left = tk.Frame(main, bg='#1E2A3A', width=250)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,4))
        left.pack_propagate(False)
        
        tk.Button(left, text="📁 Load Data Folder",
                  command=self._load_data,
                  bg='#27AE60', fg='white', font=('Helvetica',10,'bold'),
                  padx=10, pady=6).pack(fill=tk.X, padx=8, pady=8)
        
        # Distance circles
        tk.Label(left, text="Distance Circles (km):", bg='#1E2A3A', fg='#90CAF9').pack(pady=(10,4))
        
        self.dist_vars = {}
        for dist in [10, 50, 100, 200, 500]:
            var = tk.BooleanVar(value=True)
            self.dist_vars[dist] = var
            tk.Checkbutton(left, text=f"{dist} km", variable=var, bg='#1E2A3A', fg='white',
                          selectcolor='#1E2A3A', command=self._update_map).pack(anchor='w', padx=20)
        
        # Source location
        tk.Label(left, text="Source Location:", bg='#1E2A3A', fg='#90CAF9').pack(pady=(10,4))
        self.source_var = tk.StringVar(value='')
        tk.Entry(left, textvariable=self.source_var, bg='#0D1B2A', fg='#E3F2FD',
                 width=20).pack(padx=8, pady=4)
        tk.Button(left, text="Set Source", command=self._update_map,
                  bg='#1565C0', fg='white', padx=8).pack(pady=4)
        
        # Station info
        tk.Label(left, text="Earthquake Events:", bg='#1E2A3A', fg='#90CAF9').pack(pady=(10,4))
        
        self.eq_listbox = tk.Listbox(left, bg='#0D1B2A', fg='#E3F2FD', height=15)
        self.eq_listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.eq_listbox.bind('<<ListboxSelect>>', self._on_select)
        
        # Stats
        self.stats_label = tk.Label(left, text="Load data to begin",
                                    bg='#1E2A3A', fg='#A5D6A7', font=('Helvetica',8))
        self.stats_label.pack(pady=8)
        
        # Right - map
        right = tk.Frame(main, bg='#1E2A3A')
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(10,8), facecolor='white')
        self.cv = FigureCanvasTkAgg(self.fig, master=right)
        self.cv.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        toolbar = tk.Frame(right, bg='#1E2A3A')
        toolbar.pack(fill=tk.X)
        NavigationToolbar2Tk(self.cv, toolbar)
        
        self._show_empty_map()
    
    def _load_data(self):
        """Load data folder"""
        folder = filedialog.askdirectory(title="Select Folder with Zip Files")
        if not folder:
            return
        
        zip_files = [f for f in os.listdir(folder) if f.endswith('.zip')]
        
        if not zip_files:
            messagebox.showwarning("No Data", "No zip files found")
            return
        
        self.earthquake_data = []
        
        for zip_file in sorted(zip_files):
            # Extract location from filename
            name = zip_file.replace('.zip', '')
            
            # Find coordinates
            lat, lon = self._get_coords(name)
            
            self.earthquake_data.append({
                'name': name,
                'zip_file': zip_file,
                'lat': lat,
                'lon': lon
            })
        
        # Update list
        self.eq_listbox.delete(0, tk.END)
        for eq in self.earthquake_data:
            self.eq_listbox.insert(tk.END, eq['name'])
        
        self.stats_label.config(text=f"{len(self.earthquake_data)} events loaded")
        
        # Select first
        if self.earthquake_data:
            self.eq_listbox.selection_set(0)
            self._on_select(None)
    
    def _get_coords(self, name):
        """Get coordinates for location name"""
        for loc, coords in LOCATION_COORDS.items():
            if loc.lower() in name.lower():
                return coords
        return (30.0, 79.0)  # Default to Uttarakhand region
    
    def _on_select(self, event):
        """Handle selection"""
        selection = self.eq_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        eq = self.earthquake_data[idx]
        
        self.source_var.set(f"{eq['lat']:.2f}, {eq['lon']:.2f}")
        self._update_map()
    
    def _show_empty_map(self):
        """Empty map"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Load data and select earthquake\nto view station map',
                ha='center', va='center', transform=ax.transAxes, fontsize=14, color='gray')
        self.cv.draw()
    
    def _update_map(self):
        """Update map with stations and distance circles"""
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
        
        # Main map axes
        ax = self.fig.add_subplot(111)
        
        # Plot source
        ax.plot(src_lon, src_lat, '*', markersize=20, color='red', label='Source')
        ax.annotate(eq['name'], (src_lon, src_lat), textcoords="offset points",
                   xytext=(10,10), fontsize=10, fontweight='bold', color='red')
        
        # Distance circles (approximate - in degrees)
        # 1 degree lat ≈ 111 km, 1 degree lon ≈ 111 * cos(lat) km
        lat_per_km = 1 / 111.0
        lon_per_km = 1 / (111.0 * np.cos(np.radians(src_lat)))
        
        colors = {10: '#00FF00', 50: '#00FFFF', 100: '#FFFF00', 200: '#FFA500', 500: '#FF0000'}
        
        for dist, var in self.dist_vars.items():
            if var.get():
                r_lat = dist * lat_per_km
                r_lon = dist * lon_per_km
                
                # Draw circle (ellipse approximation)
                theta = np.linspace(0, 2*np.pi, 100)
                circle_lat = src_lat + r_lat * np.sin(theta)
                circle_lon = src_lon + r_lon * np.cos(theta)
                
                ax.plot(circle_lon, circle_lat, '--', color=colors[dist], 
                       linewidth=1.5, alpha=0.7, label=f'{dist} km')
        
        # Add some example station locations (based on typical Indian seismic network)
        stations = self._get_station_locations(eq['name'])
        for st_name, (st_lat, st_lon) in stations.items():
            dist = self._calculate_distance(src_lat, src_lon, st_lat, st_lon)
            ax.plot(st_lon, st_lat, 'o', markersize=8, color='blue')
            ax.annotate(f"{st_name}\n({dist:.0f}km)", (st_lon, st_lat), 
                       textcoords="offset points", xytext=(5,5), fontsize=7)
        
        # Map settings
        ax.set_xlabel('Longitude (°E)', fontsize=10)
        ax.set_ylabel('Latitude (°N)', fontsize=10)
        ax.set_title(f"Station Locations - {eq['name']}\nSource: {src_lat:.2f}°N, {src_lon:.2f}°E",
                    fontsize=12, fontweight='bold')
        ax.legend(loc='lower left', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # Set view limits
        margin = 2.0
        ax.set_xlim(src_lon - margin, src_lon + margin)
        ax.set_ylim(src_lat - margin, src_lat + margin)
        ax.set_aspect('equal')
        
        self.fig.tight_layout()
        self.cv.draw()
    
    def _get_station_locations(self, eq_name):
        """Get station locations for an earthquake"""
        # Sample station locations (in real app, extract from zip data)
        common_stations = {
            'BAG': (29.85, 79.87),  # Bageshwar
            'CHM': (30.33, 79.33),  # Chamoli
            'DPR': (29.44, 79.44),  # Dehradun
            'HAL': (29.95, 79.53),  # Haldwani
            'KGR': (30.21, 78.78),  # Tehri
            'LHW': (30.45, 78.12),  # Uttarkashi
            'RNK': (29.62, 79.41),  # Ranikhet
        }
        return common_stations
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance in km"""
        R = 6371  # Earth radius in km
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        return R * c


if __name__ == "__main__":
    root = tk.Tk()
    app = StationMapApp(root)
    root.mainloop()