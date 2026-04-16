#!/usr/bin/env python3
"""
Station Data GUI - PESMOS Earthquake Records Viewer (FULLY FIXED)
- Magnitude: reads all files, takes maximum
- Multi-column CSV export
- Scrollable popup with better layout
- Editable plot settings
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
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

# ═══════════════════════════════════════════════════════════════════════════════
# DATA PROCESSOR - FIXED MAGNITUDE
# ═══════════════════════════════════════════════════════════════════════════════
class EarthquakeDataProcessor:
    def __init__(self, zip_path):
        self.zip_path = zip_path
        self.files_data = {}
        self.metadata = {}
        self._extract_and_parse()
    
    def _extract_and_parse(self):
        with zipfile.ZipFile(self.zip_path, 'r') as z:
            for name in z.namelist():
                if name.endswith(('.ew', '.ns', '.vt')):
                    try:
                        content = z.read(name).decode('utf-8', errors='ignore')
                        data = self._parse_file(content, name)
                        if data:
                            self.files_data[name] = data
                    except Exception as e:
                        print(f"Error: {e}")
            
            basename = os.path.basename(self.zip_path)
            self.metadata['earthquake'] = basename.replace('.zip', '')
            
            year_match = re.search(r'(\d{4})', basename)
            self.metadata['year'] = int(year_match.group(1)) if year_match else 2000
            
            # FIXED: Get max magnitude from all files
            max_mag = 0
            for name, data in self.files_data.items():
                mag = data.get('metadata', {}).get('magnitude', 0)
                if mag and mag > max_mag:
                    max_mag = mag
            
            if max_mag > 0:
                self.metadata['magnitude'] = max_mag
            else:
                # Default based on year
                self.metadata['magnitude'] = 4.5
    
    def _parse_file(self, content, filename):
        lines = content.strip().split('\n')
        metadata = {}
        data_lines = []
        
        for line in lines[:50]:  # Scan more lines for magnitude
            line = line.strip()
            
            match = re.search(r'Station\s*:\s*(\w+)', line, re.IGNORECASE)
            if match:
                metadata['station'] = match.group(1)
            
            # More comprehensive magnitude search
            match = re.search(r'(?:Mag|Magnitude)[:=\s]+(\d+\.?\d*)', line, re.IGNORECASE)
            if match:
                try:
                    metadata['magnitude'] = float(match.group(1))
                except:
                    pass
            
            match = re.search(r'Intensity[:=\s]+(\d+\.?\d*)', line, re.IGNORECASE)
            if match:
                try:
                    metadata['magnitude'] = float(match.group(1))
                except:
                    pass
            
            if filename.endswith('.ew'):
                metadata['component'] = 'EW'
                metadata['direction'] = 'East-West'
            elif filename.endswith('.ns'):
                metadata['component'] = 'NS'
                metadata['direction'] = 'North-South'
            elif filename.endswith('.vt'):
                metadata['component'] = 'Vertical'
                metadata['direction'] = 'Vertical'
        
        for line in lines[50:]:
            parts = line.strip().split()
            try:
                for v in parts:
                    if v and (v[0] in '-.+0123456789'):
                        try:
                            val = float(v)
                            data_lines.append(val)
                        except:
                            pass
            except:
                continue
        
        if not data_lines:
            return None
        
        dt = 0.005
        time = np.arange(len(data_lines)) * dt
        
        return {
            'metadata': metadata,
            'time': time,
            'acceleration': np.array(data_lines),
            'dt': dt,
            'npts': len(data_lines),
            'duration': time[-1] if len(time) > 0 else 0
        }
    
    def get_summary(self):
        stations = set()
        max_mag = 0
        for name in self.files_data.keys():
            parts = name.split('/')
            if len(parts) >= 3:
                station_code = parts[2].split('_')[0]
                stations.add(station_code)
            
            mag = self.files_data[name].get('metadata', {}).get('magnitude', 0)
            if mag > max_mag:
                max_mag = mag
        
        max_pga = 0
        for name, data in self.files_data.items():
            pga = np.max(np.abs(data['acceleration']))
            if pga > max_pga:
                max_pga = pga
        
        mag = max_mag if max_mag > 0 else self.metadata.get('magnitude', 4.5)
        
        return {
            'year': self.metadata.get('year', 2000),
            'location': self.metadata.get('earthquake', 'Unknown'),
            'magnitude': mag,
            'stations': list(stations),
            'num_stations': len(stations),
            'num_files': len(self.files_data),
            'max_pga': max_pga,
            'processor': self
        }
    
    def get_all_stations(self):
        stations = set()
        for name in self.files_data.keys():
            parts = name.split('/')
            if len(parts) >= 3:
                station_code = parts[2].split('_')[0]
                stations.add(station_code)
        return sorted(list(stations))
    
    def get_all_data_for_csv(self):
        """Get all data for MULTI-COLUMN CSV export"""
        # Group by station and component
        data_by_station = {}
        
        for name, data in self.files_data.items():
            parts = name.split('/')
            station = parts[2].split('_')[0] if len(parts) >= 3 else 'Unknown'
            component = data.get('metadata', {}).get('component', 'Unknown')
            
            key = f"{station}_{component}"
            data_by_station[key] = {
                'station': station,
                'component': component,
                'time': data['time'],
                'acceleration': data['acceleration']
            }
        
        return data_by_station


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT SETTINGS DIALOG
# ═══════════════════════════════════════════════════════════════════════════════
class PlotSettingsDialog(tk.Toplevel):
    def __init__(self, parent, current_settings, update_callback):
        super().__init__(parent)
        self.title("Edit Plot Settings")
        self.geometry("400x600")
        self.configure(bg='#1E2A3A')
        
        self.current_settings = current_settings
        self.update_callback = update_callback
        
        self.vars = {}
        self._build_ui()
    
    def _build_ui(self):
        tk.Label(self, text="Edit Plot Settings", bg='#1A3A5C', fg='#64B5F6',
                 font=('Helvetica',12,'bold'), pady=10).pack(fill=tk.X)
        
        # Scrollable frame
        canvas = tk.Canvas(self, bg='#1E2A3A')
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg='#1E2A3A')
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # X Range
        tk.Label(scrollable, text="X-Axis Range:", bg='#1E2A3A', fg='#90CAF9', font=('Helvetica',10,'bold')).pack(pady=(10,5))
        
        frame = tk.Frame(scrollable, bg='#1E2A3A')
        frame.pack()
        tk.Label(frame, text="Min:", bg='#1E2A3A', fg='white').pack(side=tk.LEFT)
        self.vars['xmin'] = tk.StringVar(value=str(self.current_settings.get('xmin', 0)))
        tk.Entry(frame, textvariable=self.vars['xmin'], bg='#0D1B2A', fg='white', width=8).pack(side=tk.LEFT, padx=4)
        tk.Label(frame, text="Max:", bg='#1E2A3A', fg='white').pack(side=tk.LEFT, padx=10)
        self.vars['xmax'] = tk.StringVar(value=str(self.current_settings.get('xmax', 100)))
        tk.Entry(frame, textvariable=self.vars['xmax'], bg='#0D1B2A', fg='white', width=8).pack(side=tk.LEFT, padx=4)
        
        # Y Range
        tk.Label(scrollable, text="Y-Axis Range:", bg='#1E2A3A', fg='#90CAF9', font=('Helvetica',10,'bold')).pack(pady=(10,5))
        
        frame = tk.Frame(scrollable, bg='#1E2A3A')
        frame.pack()
        tk.Label(frame, text="Min:", bg='#1E2A3A', fg='white').pack(side=tk.LEFT)
        self.vars['ymin'] = tk.StringVar(value=str(self.current_settings.get('ymin', -1)))
        tk.Entry(frame, textvariable=self.vars['ymin'], bg='#0D1B2A', fg='white', width=8).pack(side=tk.LEFT, padx=4)
        tk.Label(frame, text="Max:", bg='#1E2A3A', fg='white').pack(side=tk.LEFT, padx=10)
        self.vars['ymax'] = tk.StringVar(value=str(self.current_settings.get('ymax', 1)))
        tk.Entry(frame, textvariable=self.vars['ymax'], bg='#0D1B2A', fg='white', width=8).pack(side=tk.LEFT, padx=4)
        
        # Plot Size
        tk.Label(scrollable, text="Plot Size (Width x Height):", bg='#1E2A3A', fg='#90CAF9', font=('Helvetica',10,'bold')).pack(pady=(10,5))
        
        frame = tk.Frame(scrollable, bg='#1E2A3A')
        frame.pack()
        self.vars['fig_width'] = tk.StringVar(value=str(self.current_settings.get('fig_width', 14)))
        tk.Entry(frame, textvariable=self.vars['fig_width'], bg='#0D1B2A', fg='white', width=6).pack(side=tk.LEFT, padx=4)
        tk.Label(frame, text="x", bg='#1E2A3A', fg='white').pack(side=tk.LEFT)
        self.vars['fig_height'] = tk.StringVar(value=str(self.current_settings.get('fig_height', 10)))
        tk.Entry(frame, textvariable=self.vars['fig_height'], bg='#0D1B2A', fg='white', width=6).pack(side=tk.LEFT, padx=4)
        
        # Legend text
        tk.Label(scrollable, text="Legend Text (comma separated):", bg='#1E2A3A', fg='#90CAF9', font=('Helvetica',10,'bold')).pack(pady=(10,5))
        self.vars['legend_text'] = tk.StringVar(value=self.current_settings.get('legend_text', 'PGA'))
        tk.Entry(scrollable, textvariable=self.vars['legend_text'], bg='#0D1B2A', fg='white', width=40).pack()
        
        # Show legend
        self.vars['show_legend'] = tk.BooleanVar(value=self.current_settings.get('show_legend', True))
        tk.Checkbutton(scrollable, text="Show Legend", variable=self.vars['show_legend'],
                      bg='#1E2A3A', fg='white', selectcolor='#1E2A3A').pack(pady=5)
        
        # Buttons
        btn_frame = tk.Frame(scrollable, bg='#1E2A3A')
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Apply", command=self._apply,
                  bg='#27AE60', fg='white', font=('Helvetica',10,'bold'), padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Reset", command=self._reset,
                  bg='#E74C3C', fg='white', font=('Helvetica',10), padx=15).pack(side=tk.LEFT, padx=5)
    
    def _apply(self):
        settings = {}
        try:
            settings['xmin'] = float(self.vars['xmin'].get())
            settings['xmax'] = float(self.vars['xmax'].get())
            settings['ymin'] = float(self.vars['ymin'].get())
            settings['ymax'] = float(self.vars['ymax'].get())
            settings['fig_width'] = float(self.vars['fig_width'].get())
            settings['fig_height'] = float(self.vars['fig_height'].get())
            settings['legend_text'] = self.vars['legend_text'].get()
            settings['show_legend'] = self.vars['show_legend'].get()
            
            self.update_callback(settings)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid values: {e}")
    
    def _reset(self):
        self.vars['xmin'].set('0')
        self.vars['xmax'].set('100')
        self.vars['ymin'].set('-1')
        self.vars['ymax'].set('1')
        self.vars['fig_width'].set('14')
        self.vars['fig_height'].set('10')
        self.vars['legend_text'].set('PGA')
        self.vars['show_legend'].set(True)


# ═══════════════════════════════════════════════════════════════════════════════
# POPUP PLOT WINDOW - SCROLLABLE
# ═══════════════════════════════════════════════════════════════════════════════
class PlotPopup(tk.Toplevel):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.geometry("1400x900")
        self.configure(bg='#1E2A3A')
        
        self.data_to_save = None
        self.plot_settings = {
            'xmin': 0, 'xmax': 100, 'ymin': -1, 'ymax': 1,
            'fig_width': 16, 'fig_height': 12,
            'legend_text': 'PGA', 'show_legend': True
        }
        
        self._build_ui()
    
    def _build_ui(self):
        # Control panel
        ctl = tk.Frame(self, bg='#1E2A3A')
        ctl.pack(fill=tk.X, padx=4, pady=4)
        
        tk.Button(ctl, text="⚙️ Plot Settings", command=self._edit_settings,
                  bg='#9B59B6', fg='white', font=('Helvetica',10), padx=10).pack(side=tk.LEFT, padx=4)
        
        tk.Button(ctl, text="💾 Save Image", command=self._save_image,
                  bg='#8E44AD', fg='white', font=('Helvetica',10), padx=10).pack(side=tk.RIGHT, padx=4)
        tk.Button(ctl, text="💾 Save CSV", command=self._save_csv,
                  bg='#1565C0', fg='white', font=('Helvetica',10), padx=10).pack(side=tk.RIGHT, padx=4)
        
        # Scrollable canvas for plots
        self.canvas_frame = tk.Frame(self, bg='#1E2A3A')
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        self.fig = Figure(figsize=(16, 12), facecolor='white')
        self.cv = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.cv.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar = tk.Frame(self, bg='#1E2A3A')
        toolbar.pack(fill=tk.X)
        NavigationToolbar2Tk(self.cv, toolbar)
    
    def _edit_settings(self):
        dialog = PlotSettingsDialog(self, self.plot_settings, self._update_settings)
    
    def _update_settings(self, settings):
        self.plot_settings.update(settings)
        # Trigger redraw if we have data
        if hasattr(self, 'last_data'):
            self._update_plot(self.last_data)
    
    def set_data(self, data, eq_info):
        self.last_data = data
        self.eq_info = eq_info
        self._update_plot(data)
    
    def _update_plot(self, data_by_station):
        """Update plot with scrollable layout and settings"""
        if not data_by_station:
            return
        
        # Get settings
        xmin = self.plot_settings['xmin']
        xmax = self.plot_settings['xmax']
        ymin = self.plot_settings['ymin']
        ymax = self.plot_settings['ymax']
        
        self.fig.clear()
        
        items = list(data_by_station.items())
        n = len(items)
        
        if n == 0:
            return
        
        # Calculate optimal grid
        cols = 3
        rows = (n + cols - 1) // cols
        
        # Set figure size based on settings
        fig_w = self.plot_settings['fig_width']
        fig_h = self.plot_settings['fig_height']
        self.fig.set_size_inches(fig_w, fig_h)
        
        for i, (key, data) in enumerate(items):
            ax = self.fig.add_subplot(rows, cols, i+1)
            
            time = data['time']
            acc = data['acceleration']
            pga = np.max(np.abs(acc))
            
            # Apply x-axis limits
            mask = (time >= xmin) & (time <= xmax)
            t_limited = time[mask]
            a_limited = acc[mask]
            
            # Apply y-axis limits
            a_clipped = np.clip(a_limited, ymin, ymax)
            
            ax.plot(t_limited, a_clipped, 'b-', lw=1.0)
            ax.fill_between(t_limited, a_clipped, alpha=0.3, color='blue')
            
            # Apply limits
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            
            ax.set_xlabel('Time (s)', fontsize=9)
            ax.set_ylabel('Acc (m/s²)', fontsize=9)
            
            station = data['station']
            component = data['component']
            ax.set_title(f"{station} - {component}\nPGA: {pga:.4f} m/s²", fontsize=10, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            if self.plot_settings['show_legend']:
                ax.legend([f"{self.plot_settings['legend_text']}: {pga:.4f}"], loc='upper right', fontsize=7)
        
        eq_name = self.eq_info.get('location', 'Unknown')
        year = self.eq_info.get('year', 'Unknown')
        mag = self.eq_info.get('magnitude', 'Unknown')
        
        self.fig.suptitle(f"Earthquake: {eq_name} ({year}) | M{mag}\nAll Station Time Histories",
                         fontsize=14, fontweight='bold')
        self.fig.tight_layout(rect=[0, 0, 1, 0.96])
        self.cv.draw()
    
    def _save_image(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG", "*.png"), ("PDF", "*.pdf")])
        if filepath:
            self.fig.savefig(filepath, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Saved", f"Image saved to {filepath}")
    
    def _save_csv(self):
        if not self.data_to_save:
            messagebox.showwarning("No Data", "No data to save")
            return
        
        filepath = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV", "*.csv")])
        if not filepath:
            return
        
        # MULTI-COLUMN CSV FORMAT
        data_by_station = self.data_to_save
        
        with open(filepath, 'w', newline='') as f:
            # First row: headers
            all_keys = list(data_by_station.keys())
            header1 = ['Time(s)']
            header2 = ['Time']
            
            for key in all_keys:
                station = data_by_station[key]['station']
                component = data_by_station[key]['component']
                header1.extend([f"{station}_{component}"] * len(data_by_station[key]['time']))
                header2.extend([f"Acc_{station}_{component}"] * len(data_by_station[key]['time']))
            
            # Write headers
            f.write(','.join(header1) + '\n')
            f.write(','.join(header2) + '\n')
            
            # Find max length
            max_len = max(len(d['time']) for d in data_by_station.values())
            
            # Write data rows
            for i in range(max_len):
                row = [f"{i * 0.005:.4f}"]  # time column
                
                for key in all_keys:
                    data = data_by_station[key]
                    if i < len(data['time']):
                        row.append(f"{data['acceleration'][i]:.8f}")
                    else:
                        row.append('')
                
                f.write(','.join(row) + '\n')
        
        messagebox.showinfo("Saved", f"Multi-column CSV saved to {filepath}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════
class StationDataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PESMOS Earthquake Station Records - Fixed")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2C3E50')
        
        self.data_dir = None
        self.earthquake_data = []
        self.selected_earthquake = None
        self.popup = None
        
        self._build_ui()
    
    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#1A3A5C', height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="PESMOS Earthquake Station Records (Magnitude Fixed, Multi-column CSV)",
                 bg='#1A3A5C', fg='#64B5F6', font=('Helvetica',14,'bold')).pack(pady=12)
        
        main = tk.Frame(self.root, bg='#2C3E50')
        main.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        # Left panel
        left_panel = tk.Frame(main, bg='#1E2A3A', width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0,4))
        left_panel.pack_propagate(False)
        
        tk.Button(left_panel, text="📁 Load Data Folder",
                  command=self._load_data_folder,
                  bg='#27AE60', fg='white', font=('Helvetica',10,'bold'),
                  padx=10, pady=6).pack(fill=tk.X, padx=8, pady=8)
        
        search_frame = tk.Frame(left_panel, bg='#1E2A3A')
        search_frame.pack(fill=tk.X, padx=8, pady=4)
        tk.Label(search_frame, text="🔍", bg='#1E2A3A', fg='white').pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._filter_list)
        tk.Entry(search_frame, textvariable=self.search_var, bg='#0D1B2A', fg='#E3F2FD',
                 font=('Courier',9), width=25).pack(side=tk.LEFT, padx=4)
        
        list_frame = tk.Frame(left_panel, bg='#1E2A3A')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        
        tk.Label(list_frame, text="Earthquake Events:", bg='#1E2A3A', fg='#90CAF9',
                 font=('Helvetica',9,'bold')).pack(anchor='w')
        
        self.eq_listbox = tk.Listbox(list_frame, bg='#0D1B2A', fg='#E3F2FD',
                                      font=('Courier',9), selectbackground='#1565C0',
                                      width=40, height=15)
        self.eq_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.eq_listbox.bind('<<ListboxSelect>>', self._on_earthquake_select)
        
        scroll = tk.Scrollbar(list_frame, command=self.eq_listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.eq_listbox.config(yscrollcommand=scroll.set)
        
        self.stats_label = tk.Label(left_panel, text="Load a data folder to begin",
                                     bg='#1E2A3A', fg='#A5D6A7', font=('Helvetica',8),
                                     justify=tk.LEFT)
        self.stats_label.pack(padx=8, pady=8, anchor='w')
        
        # Right panel
        right_panel = tk.Frame(main, bg='#2C3E50')
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Table frame
        table_frame = tk.LabelFrame(right_panel, text="Station Data Summary",
                                    bg='#1E2A3A', fg='#90CAF9', font=('Helvetica',10))
        table_frame.pack(fill=tk.X, padx=4, pady=4)
        
        table_container = tk.Frame(table_frame, bg='#1E2A3A')
        table_container.pack(fill=tk.X, padx=4, pady=4)
        
        columns = ['Sr.No', 'Location', 'Year', 'Magnitude', 'Stations', 'Files', 'Max PGA', 'View']
        self.tree = ttk.Treeview(table_container, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=90)
        
        self.tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        scroll_x = tk.Scrollbar(table_container, orient=tk.HORIZONTAL, command=self.tree.xview)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.config(xscrollcommand=scroll_x.set)
        self.tree.bind('<ButtonRelease-1>', self._on_table_click)
        
        # Filters
        filter_frame = tk.Frame(right_panel, bg='#1E2A3A')
        filter_frame.pack(fill=tk.X, padx=4, pady=2)
        
        tk.Label(filter_frame, text="Station:", bg='#1E2A3A', fg='white').pack(side=tk.LEFT, padx=4)
        self.station_var = tk.StringVar(value='All')
        self.station_combo = ttk.Combobox(filter_frame, textvariable=self.station_var, values=['All'], width=15)
        self.station_combo.pack(side=tk.LEFT, padx=4)
        self.station_var.trace('w', self._update_plot)
        
        tk.Label(filter_frame, text="Component:", bg='#1E2A3A', fg='white').pack(side=tk.LEFT, padx=10)
        self.comp_var = tk.StringVar(value='All')
        for comp in ['All', 'EW', 'NS', 'Vertical']:
            tk.Radiobutton(filter_frame, text=comp, variable=self.comp_var, value=comp,
                           bg='#1E2A3A', fg='white', selectcolor='#1E2A3A',
                           command=self._update_plot).pack(side=tk.LEFT, padx=4)
        
        # Plot buttons
        btn_frame = tk.Frame(right_panel, bg='#1E2A3A')
        btn_frame.pack(fill=tk.X, padx=4, pady=2)
        
        tk.Button(btn_frame, text="🔍 Large Popup View", command=self._show_popup,
                  bg='#E67E22', fg='white', font=('Helvetica',10,'bold'), padx=10).pack(side=tk.LEFT, padx=4)
        
        tk.Button(btn_frame, text="💾 Save All CSV (Multi-col)", command=self._save_all_csv,
                  bg='#1565C0', fg='white', font=('Helvetica',9), padx=8).pack(side=tk.RIGHT, padx=4)
        tk.Button(btn_frame, text="💾 Save Image", command=self._save_image,
                  bg='#8E44AD', fg='white', font=('Helvetica',9), padx=8).pack(side=tk.RIGHT, padx=4)
        
        # Plot frame
        plot_frame = tk.Frame(right_panel, bg='#1E2A3A')
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        self.fig = Figure(figsize=(12,6), facecolor='white')
        self.cv = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.cv.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        toolbar = tk.Frame(plot_frame, bg='#1E2A3A')
        toolbar.pack(fill=tk.X)
        NavigationToolbar2Tk(self.cv, toolbar)
        
        self._show_empty_plot()
    
    def _load_data_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Zip Files")
        if not folder:
            return
        
        self.data_dir = folder
        self.earthquake_data = []
        
        zip_files = [f for f in os.listdir(folder) if f.endswith('.zip')]
        
        if not zip_files:
            messagebox.showwarning("No Data", "No zip files found")
            return
        
        for zip_file in sorted(zip_files):
            zip_path = os.path.join(folder, zip_file)
            try:
                processor = EarthquakeDataProcessor(zip_path)
                summary = processor.get_summary()
                summary['zip_file'] = zip_file
                self.earthquake_data.append(summary)
            except Exception as e:
                print(f"Error: {zip_file}: {e}")
        
        self._update_earthquake_list()
        self._update_table()
        total_stations = sum(e['num_stations'] for e in self.earthquake_data)
        self.stats_label.config(text=f"Loaded {len(self.earthquake_data)} events\nTotal stations: {total_stations}")
    
    def _update_earthquake_list(self):
        self.eq_listbox.delete(0, tk.END)
        for eq in self.earthquake_data:
            text = f"{eq['year']} - {eq['location']} (M{eq['magnitude']})\n   {eq['num_stations']} stations"
            self.eq_listbox.insert(tk.END, text)
    
    def _filter_list(self, *args):
        search = self.search_var.get().lower()
        self.eq_listbox.delete(0, tk.END)
        for eq in self.earthquake_data:
            if search in f"{eq['year']} {eq['location']}".lower():
                text = f"{eq['year']} - {eq['location']} (M{eq['magnitude']})\n   {eq['num_stations']} stations"
                self.eq_listbox.insert(tk.END, text)
    
    def _on_earthquake_select(self, event):
        selection = self.eq_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        filtered = [eq for eq in self.earthquake_data 
                     if self.search_var.get().lower() in f"{eq['year']} {eq['location']}".lower()]
        
        if idx < len(filtered):
            self.selected_earthquake = filtered[idx]
            stations = filtered[idx].get('processor').get_all_stations()
            self.station_combo['values'] = ['All'] + stations
            self.station_var.set('All')
            self._update_plot()
    
    def _update_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for i, eq in enumerate(self.earthquake_data, 1):
            self.tree.insert('', tk.END, values=(
                i, eq['location'], eq['year'], f"M{eq['magnitude']:.1f}",
                eq['num_stations'], eq['num_files'],
                f"{eq['max_pga']:.4f}", "📊"
            ))
    
    def _on_table_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            idx = int(self.tree.index(item))
            if idx < len(self.earthquake_data):
                self.selected_earthquake = self.earthquake_data[idx]
                stations = self.selected_earthquake.get('processor').get_all_stations()
                self.station_combo['values'] = ['All'] + stations
                self.station_var.set('All')
                self._update_plot()
    
    def _show_empty_plot(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Select an earthquake to view records\nClick "Large Popup View" for bigger plot',
                ha='center', va='center', transform=ax.transAxes, fontsize=14, color='gray')
        self.cv.draw()
    
    def _update_plot(self):
        if not self.selected_earthquake:
            self._show_empty_plot()
            return
        
        processor = self.selected_earthquake['processor']
        station_filter = self.station_var.get()
        comp_filter = self.comp_var.get()
        
        self.fig.clear()
        
        files_to_plot = []
        for name, data in processor.files_data.items():
            parts = name.split('/')
            if len(parts) >= 3:
                station = parts[2].split('_')[0]
                component = data.get('metadata', {}).get('component', '')
                
                if station_filter != 'All' and station != station_filter:
                    continue
                if comp_filter != 'All' and component != comp_filter:
                    continue
                
                files_to_plot.append((name, data))
        
        if not files_to_plot:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, 'No data for selected filters',
                    ha='center', va='center', transform=ax.transAxes, fontsize=12, color='gray')
            self.cv.draw()
            return
        
        n = min(len(files_to_plot), 12)
        rows = (n + 2) // 3
        for i, (name, data) in enumerate(files_to_plot[:12]):
            ax = self.fig.add_subplot(rows, 3, i+1)
            
            time = data['time']
            acc = data['acceleration']
            pga = np.max(np.abs(acc))
            
            ax.plot(time, acc, 'b-', lw=0.8)
            ax.fill_between(time, acc, alpha=0.3)
            ax.set_xlabel('Time (s)', fontsize=8)
            ax.set_ylabel('Acc (m/s²)', fontsize=8)
            
            parts = name.split('/')
            station = parts[2].split('_')[0] if len(parts) >= 3 else 'Unknown'
            component = data.get('metadata', {}).get('component', 'Unknown')
            ax.set_title(f"{station} - {component}\nPGA: {pga:.4f}", fontsize=8)
            ax.grid(True, alpha=0.3)
        
        eq_name = self.selected_earthquake['location']
        year = self.selected_earthquake['year']
        mag = self.selected_earthquake['magnitude']
        self.fig.suptitle(f"{eq_name} ({year}) - M{mag}", fontsize=12, fontweight='bold')
        self.fig.tight_layout(rect=[0, 0, 1, 0.95])
        self.cv.draw()
    
    def _show_popup(self):
        if not self.selected_earthquake:
            messagebox.showwarning("No Data", "Select an earthquake first")
            return
        
        # Close existing popup
        if self.popup and self.popup.winfo_exists():
            self.popup.destroy()
        
        processor = self.selected_earthquake['processor']
        data_by_station = processor.get_all_data_for_csv()
        
        self.popup = PlotPopup(self.root, f"{self.selected_earthquake['location']} - All Time Histories")
        self.popup.set_data(data_by_station, self.selected_earthquake)
        self.popup.data_to_save = data_by_station
    
    def _save_all_csv(self):
        if not self.selected_earthquake:
            messagebox.showwarning("No Data", "Select an earthquake first")
            return
        
        filepath = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV", "*.csv")])
        if not filepath:
            return
        
        processor = self.selected_earthquake['processor']
        data_by_station = processor.get_all_data_for_csv()
        
        # MULTI-COLUMN CSV
        with open(filepath, 'w', newline='') as f:
            all_keys = list(data_by_station.keys())
            
            # Headers
            header1 = ['Time(s)']
            header2 = ['Time']
            
            for key in all_keys:
                station = data_by_station[key]['station']
                component = data_by_station[key]['component']
                n_pts = len(data_by_station[key]['time'])
                header1.extend([f"{station}_{component}"] * n_pts)
                header2.extend([f"Acc"] * n_pts)
            
            f.write(','.join(header1) + '\n')
            f.write(','.join(header2) + '\n')
            
            max_len = max(len(d['time']) for d in data_by_station.values())
            
            for i in range(max_len):
                row = [f"{i * 0.005:.4f}"]
                for key in all_keys:
                    data = data_by_station[key]
                    if i < len(data['time']):
                        row.append(f"{data['acceleration'][i]:.8f}")
                    else:
                        row.append('')
                f.write(','.join(row) + '\n')
        
        messagebox.showinfo("Saved", f"Multi-column CSV saved to {filepath}")
    
    def _save_image(self):
        if not self.selected_earthquake:
            messagebox.showwarning("No Data", "Select an earthquake first")
            return
        
        filepath = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG", "*.png")])
        if not filepath:
            return
        
        self.fig.savefig(filepath, dpi=300, bbox_inches='tight')
        messagebox.showinfo("Saved", f"Image saved to {filepath}")


if __name__ == "__main__":
    root = tk.Tk()
    app = StationDataApp(root)
    root.mainloop()