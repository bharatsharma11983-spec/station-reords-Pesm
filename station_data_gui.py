#!/usr/bin/env python3
"""
Station Data GUI - FINAL VERSION v2
- Fixed trace_add() for Tcl 9 compatibility
- Fixed callback arguments
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import zipfile
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import re
import csv
import math


class EarthquakeDataProcessor:
    def __init__(self, zip_path):
        self.zip_path = zip_path
        self.raw_data = {}
        self.metadata = {}
        self._extract_and_parse()
    
    def _extract_and_parse(self):
        with zipfile.ZipFile(self.zip_path, 'r') as z:
            for name in z.namelist():
                if name.endswith(('.ew', '.ns', '.vt')):
                    try:
                        content = z.read(name).decode('utf-8', errors='ignore')
                        data = self._parse_file(content, name)
                        if data is not None:
                            self.raw_data[name] = data
                    except Exception as e:
                        print(f"Error: {name}: {e}")
            
            basename = os.path.basename(self.zip_path)
            self.metadata['earthquake'] = basename.replace('.zip', '')
            
            year_match = re.search(r'(\d{4})', basename)
            self.metadata['year'] = int(year_match.group(1)) if year_match else 2000
            
            max_mag = 0
            for name, data in self.raw_data.items():
                if data.get('magnitude', 0) > max_mag:
                    max_mag = data['magnitude']
            
            self.metadata['magnitude'] = max_mag if max_mag > 0 else 4.5
    
    def _parse_file(self, content, filename):
        lines = content.strip().split('\n')
        metadata = {}
        values = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                try:
                    val = float(part)
                    values.append(val)
                except:
                    pass
            
            parts = filename.split('/')
            if len(parts) >= 2:
                metadata['station'] = parts[-1].split('.')[0]
        
        if not values:
            return None
        
        if filename.endswith('.ew'):
            metadata['component'] = 'EW'
        elif filename.endswith('.ns'):
            metadata['component'] = 'NS'
        elif filename.endswith('.vt'):
            metadata['component'] = 'V'
        
        dt = 0.005
        time = np.arange(len(values)) * dt
        
        return {
            'acceleration': np.array(values),
            'time': time,
            'dt': dt,
            'station': metadata.get('station', 'Unknown'),
            'component': metadata.get('component', 'Unknown'),
            'magnitude': metadata.get('magnitude', 0)
        }
    
    def get_summary(self):
        stations = set()
        for name, data in self.raw_data.items():
            stations.add(data.get('station', 'Unknown'))
        
        max_pga = 0
        for name, data in self.raw_data.items():
            pga = np.max(np.abs(data['acceleration']))
            if pga > max_pga:
                max_pga = pga
        
        return {
            'year': self.metadata.get('year', 2000),
            'location': self.metadata.get('earthquake', 'Unknown'),
            'magnitude': self.metadata.get('magnitude', 4.5),
            'stations': list(stations),
            'num_stations': len(stations),
            'num_files': len(self.raw_data),
            'max_pga': max_pga,
            'processor': self
        }
    
    def get_all_stations(self):
        stations = set()
        for name, data in self.raw_data.items():
            stations.add(data.get('station', 'Unknown'))
        return sorted(list(stations))
    
    def get_data_by_station(self):
        data_by_station = {}
        for name, data in self.raw_data.items():
            station = data.get('station', 'Unknown')
            component = data.get('component', 'Unknown')
            
            if station not in data_by_station:
                data_by_station[station] = {}
            data_by_station[station][component] = data
        
        return data_by_station


class LargePlotPopup(tk.Toplevel):
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.geometry("1500x1000")
        self.configure(bg='#1E2A3A')
        
        self.plot_settings = {
            'xmin': 0, 'xmax': 60, 'ymin': -1, 'ymax': 1,
            'fig_width': 16, 'fig_height': 12,
            'legend_text': 'PGA', 'show_legend': True
        }
        self.data_by_station = None
        self.eq_info = None
        
        self._build_ui()
    
    def _build_ui(self):
        ctl = tk.Frame(self, bg='#1E2A3A', height=50)
        ctl.pack(fill=tk.X, padx=4, pady=4)
        
        tk.Button(ctl, text="⚙️ Plot Settings", command=self._edit_settings,
                bg='#9B59B6', fg='white', font=('Helvetica',10), padx=10).pack(side=tk.LEFT, padx=4)
        
        tk.Button(ctl, text="💾 Save Image", command=self._save_image,
                bg='#8E44AD', fg='white', font=('Helvetica',10), padx=10).pack(side=tk.RIGHT, padx=4)
        
        self.canvas_frame = tk.Frame(self, bg='white')
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg='white')
        self.v_scroll = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.h_scroll = tk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.plot_inner = tk.Frame(self.canvas, bg='white')
        self.canvas.create_window((0, 0), window=self.plot_inner, anchor='nw')
        
        self.fig = None
        self.cv = None
    
    def _edit_settings(self):
        dialog = PlotSettingsDialog(self, self.plot_settings, self._update_settings)
    
    def _update_settings(self, settings):
        self.plot_settings.update(settings)
        if self.data_by_station:
            self._render_plots()
    
    def set_data(self, data_by_station, eq_info):
        self.data_by_station = data_by_station
        self.eq_info = eq_info
        self._render_plots()
    
    def _render_plots(self):
        for w in self.plot_inner.winfo_children():
            w.destroy()
        
        if not self.data_by_station:
            return
        
        xmin = self.plot_settings['xmin']
        xmax = self.plot_settings['xmax']
        ymin = self.plot_settings['ymin']
        ymax = self.plot_settings['ymax']
        
        stations = list(self.data_by_station.keys())
        n = len(stations)
        cols = 3
        rows = math.ceil(n / cols)
        
        fig_w = self.plot_settings['fig_width']
        fig_h = rows * 3.5
        
        self.fig = Figure(figsize=(fig_w, fig_h), facecolor='white')
        
        for idx, station in enumerate(stations):
            components = self.data_by_station[station]
            
            for comp_idx, (comp, comp_data) in enumerate(components.items()):
                ax = self.fig.add_subplot(rows * 3, cols, idx * 3 + comp_idx + 1)
                
                time = comp_data['time']
                acc = comp_data['acceleration']
                pga = np.max(np.abs(acc))
                
                mask = (time >= xmin) & (time <= xmax)
                t_plot = time[mask]
                a_plot = np.clip(acc[mask], ymin, ymax)
                
                ax.plot(t_plot, a_plot, 'b-', lw=0.8)
                ax.fill_between(t_plot, a_plot, alpha=0.3)
                ax.set_xlim(xmin, xmax)
                ax.set_ylim(ymin, ymax)
                ax.set_xlabel('Time (s)', fontsize=8)
                ax.set_ylabel('Acc (m/s²)', fontsize=8)
                ax.set_title(f"{station} - {comp}\nPGA: {pga:.4f}", fontsize=9, fontweight='bold')
                ax.grid(True, alpha=0.3)
        
        year = self.eq_info.get('year', 'Unknown')
        mag = self.eq_info.get('magnitude', 'Unknown')
        loc = self.eq_info.get('location', 'Unknown')
        
        self.fig.suptitle(f"{loc} ({year}) M{mag} - All Station Records", fontsize=14, fontweight='bold')
        self.fig.tight_layout(rect=[0, 0, 1, 0.95])
        
        self.cv = FigureCanvasTkAgg(self.fig, master=self.plot_inner)
        self.cv.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.plot_inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def _save_image(self):
        if not self.fig:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            self.fig.savefig(path, dpi=300, bbox_inches='tight')
            messagebox.showinfo("Saved", f"Image saved to {path}")


class PlotSettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings, update_callback):
        super().__init__(parent)
        self.title("Plot Settings")
        self.geometry("400x500")
        self.configure(bg='#1E2A3A')
        
        self.settings = settings
        self.callback = update_callback
        self.vars = {}
        
        self._build_ui()
    
    def _build_ui(self):
        canvas = tk.Canvas(self, bg='#1E2A3A')
        scroll = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg='#1E2A3A')
        
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor='nw')
        canvas.configure(yscrollcommand=scroll.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
        tk.Label(frame, text="Plot Settings", bg='#1A3A5C', fg='#64B5F6',
                font=('Helvetica',12,'bold'), pady=10).pack()
        
        self._add_entry(frame, "xmin", "X Min:", str(self.settings.get('xmin', 0)))
        self._add_entry(frame, "xmax", "X Max:", str(self.settings.get('xmax', 60)))
        self._add_entry(frame, "ymin", "Y Min:", str(self.settings.get('ymin', -1)))
        self._add_entry(frame, "ymax", "Y Max:", str(self.settings.get('ymax', 1)))
        self._add_entry(frame, "fig_width", "Width:", str(self.settings.get('fig_width', 14)))
        self._add_entry(frame, "fig_height", "Height:", str(self.settings.get('fig_height', 10)))
        self._add_entry(frame, "legend_text", "Legend:", self.settings.get('legend_text', 'PGA'))
        self._add_check(frame, "show_legend", "Show Legend:", self.settings.get('show_legend', True))
        
        btns = tk.Frame(frame, bg='#1E2A3A')
        btns.pack(pady=15)
        tk.Button(btns, text="Apply", command=self._apply, bg='#27AE60', fg='white', padx=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="Reset", command=self._reset, bg='#E74C3C', fg='white', padx=15).pack(side=tk.LEFT, padx=5)
    
    def _add_entry(self, parent, key, label, default):
        f = tk.Frame(parent, bg='#1E2A3A')
        f.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(f, text=label, bg='#1E2A3A', fg='white', width=12, anchor='w').pack(side=tk.LEFT)
        self.vars[key] = tk.StringVar(value=default)
        tk.Entry(f, textvariable=self.vars[key], bg='#0D1B2A', fg='white').pack(side=tk.LEFT)
    
    def _add_check(self, parent, key, label, default):
        f = tk.Frame(parent, bg='#1E2A3A')
        f.pack(fill=tk.X, padx=10, pady=3)
        self.vars[key] = tk.BooleanVar(value=default)
        tk.Checkbutton(f, text=label, variable=self.vars[key], bg='#1E2A3A', fg='white',
                    selectcolor='#1E2A3A').pack(side=tk.LEFT)
    
    def _apply(self):
        try:
            new_settings = {}
            for key, var in self.vars.items():
                val = var.get()
                if key in ['xmin', 'xmax', 'ymin', 'ymax', 'fig_width', 'fig_height']:
                    new_settings[key] = float(val)
                elif key in ['show_legend']:
                    new_settings[key] = bool(val)
                else:
                    new_settings[key] = str(val)
            self.callback(new_settings)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _reset(self):
        self.vars['xmin'].set('0')
        self.vars['xmax'].set('60')
        self.vars['ymin'].set('-1')
        self.vars['ymax'].set('1')
        self.vars['fig_width'].set('14')
        self.vars['fig_height'].set('10')
        self.vars['legend_text'].set('PGA')
        self.vars['show_legend'].set(True)


class StationDataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PESMOS Station Records - FINAL v2")
        self.root.geometry("1500x1000")
        self.root.configure(bg='#2C3E50')
        
        self.data_dir = None
        self.earthquake_data = []
        self.selected_earthquake = None
        self.popup = None
        
        self._build_ui()
    
    def _build_ui(self):
        tk.Label(self.root, text="PESMOS Station Records - FINAL v2",
               bg='#1A3A5C', fg='#64B5F6', font=('Helvetica',14,'bold'), pady=10).pack(fill=tk.X)
        
        main = tk.Frame(self.root, bg='#2C3E50')
        main.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        left = tk.Frame(main, bg='#1E2A3A', width=300)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,4))
        left.pack_propagate(False)
        
        tk.Button(left, text="📁 Load Data Folder", command=self._load_folder,
                bg='#27AE60', fg='white', font=('Helvetica',10,'bold'), padx=10, pady=6).pack(fill=tk.X, padx=8, pady=8)
        
        tk.Label(left, text="🔍 Search:", bg='#1E2A3A', fg='#90CAF9').pack(pady=(5,0))
        self.search_var = tk.StringVar()
        # Use trace_add instead of deprecated trace
        self.search_var.trace_add('write', self._filter_list)
        tk.Entry(left, textvariable=self.search_var, bg='#0D1B2A', fg='white', width=30).pack(padx=8, pady=4)
        
        tk.Label(left, text="Earthquakes:", bg='#1E2A3A', fg='#90CAF9', font=('Helvetica',10,'bold')).pack(pady=(10,4))
        self.eq_list = tk.Listbox(left, bg='#0D1B2A', fg='#E3F2FD', height=10)
        self.eq_list.pack(fill=tk.BOTH, expand=True, padx=8)
        self.eq_list.bind('<<ListboxSelect>>', self._on_eq_select)
        
        self.stats = tk.Label(left, text="Load data folder to begin",
                        bg='#1E2A3A', fg='#A5D6A7', font=('Helvetica',8))
        self.stats.pack(pady=8, padx=8, anchor='w')
        
        right = tk.Frame(main, bg='#2C3E50')
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        filter_frame = tk.Frame(right, bg='#1E2A3A')
        filter_frame.pack(fill=tk.X, padx=4, pady=4)
        
        tk.Label(filter_frame, text="Station:", bg='#1E2A3A', fg='white').pack(side=tk.LEFT, padx=5)
        self.station_var = tk.StringVar(value='All')
        self.station_combo = ttk.Combobox(filter_frame, textvariable=self.station_var, values=['All'], width=15)
        self.station_combo.pack(side=tk.LEFT, padx=5)
        self.station_var.trace_add('write', self._update_plot)
        
        tk.Label(filter_frame, text="Component:", bg='#1E2A3A', fg='white').pack(side=tk.LEFT, padx=15)
        self.comp_var = tk.StringVar(value='All')
        for comp in ['All', 'EW', 'NS', 'V']:
            tk.Radiobutton(filter_frame, text=comp, variable=self.comp_var, value=comp,
                       bg='#1E2A3A', fg='white', selectcolor='#1E2A3A',
                       command=self._update_plot).pack(side=tk.LEFT, padx=3)
        
        btn_frame = tk.Frame(right, bg='#1E2A3A')
        btn_frame.pack(fill=tk.X, padx=4)
        
        tk.Button(btn_frame, text="🔍 Large Scrollable Popup", command=self._show_large_popup,
                bg='#E67E22', fg='white', font=('Helvetica',10,'bold'), padx=10).pack(side=tk.LEFT, padx=4)
        
        tk.Button(btn_frame, text="💾 Save CSV (per station)", command=self._save_csv,
                bg='#1565C0', fg='white', padx=10).pack(side=tk.RIGHT, padx=4)
        
        plot_frame = tk.Frame(right, bg='#1E2A3A')
        plot_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        self.fig = Figure(figsize=(14,8), facecolor='white')
        self.cv = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.cv.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        tb = tk.Frame(plot_frame, bg='#1E2A3A')
        tb.pack(fill=tk.X)
        NavigationToolbar2Tk(self.cv, tb)
        
        self._show_empty()
    
    def _load_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Zip Files")
        if not folder:
            return
        
        self.data_dir = folder
        zip_files = [f for f in os.listdir(folder) if f.endswith('.zip')]
        
        if not zip_files:
            messagebox.showwarning("Warning", "No zip files found")
            return
        
        self.earthquake_data = []
        for zf in sorted(zip_files):
            try:
                proc = EarthquakeDataProcessor(os.path.join(folder, zf))
                summary = proc.get_summary()
                summary['zip_file'] = zf
                self.earthquake_data.append(summary)
            except Exception as e:
                print(f"Error: {zf}: {e}")
        
        self._update_eq_list()
        total = sum(e['num_stations'] for e in self.earthquake_data)
        self.stats.config(text=f"Loaded {len(self.earthquake_data)} events, {total} stations")
    
    def _update_eq_list(self):
        self.eq_list.delete(0, tk.END)
        for eq in self.earthquake_data:
            txt = f"{eq['year']} {eq['location']} M{eq['magnitude']:.1f}"
            self.eq_list.insert(tk.END, txt)
    
    def _filter_list(self, *args):
        search = self.search_var.get().lower()
        self.eq_list.delete(0, tk.END)
        for eq in self.earthquake_data:
            if search in f"{eq['year']} {eq['location']}".lower():
                txt = f"{eq['year']} {eq['location']} M{eq['magnitude']:.1f}"
                self.eq_list.insert(tk.END, txt)
    
    def _on_eq_select(self, event):
        sel = self.eq_list.curselection()
        if not sel:
            return
        
        idx = sel[0]
        filtered = [eq for eq in self.earthquake_data 
                   if self.search_var.get().lower() in f"{eq['year']} {eq['location']}".lower()]
        
        if idx < len(filtered):
            self.selected_earthquake = filtered[idx]
            stations = filtered[idx].get('processor').get_all_stations()
            self.station_combo['values'] = ['All'] + stations
            self.station_var.set('All')
            self._update_plot()
    
    def _show_empty(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, 'Select earthquake to view records',
               ha='center', va='center', transform=ax.transAxes, fontsize=14, color='gray')
        self.cv.draw()
    
    def _update_plot(self, *args):
        if not self.selected_earthquake:
            self._show_empty()
            return
        
        proc = self.selected_earthquake['processor']
        station = self.station_var.get()
        comp = self.comp_var.get()
        
        data = proc.get_data_by_station()
        
        if station != 'All':
            data = {station: data.get(station, {})}
        
        self.fig.clear()
        
        files = []
        for st, comps in data.items():
            for c, d in comps.items():
                if comp != 'All' and c != comp:
                    continue
                files.append((st, c, d))
        
        if not files:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, 'No data found', ha='center', va='center',
                   transform=ax.transAxes, fontsize=12, color='gray')
            self.cv.draw()
            return
        
        n = min(len(files), 12)
        rows = (n + 2) // 3
        
        for i, (st, c, d) in enumerate(files[:12]):
            ax = self.fig.add_subplot(rows, 3, i+1)
            ax.plot(d['time'], d['acceleration'], 'b-', lw=0.8)
            ax.fill_between(d['time'], d['acceleration'], alpha=0.3)
            pga = np.max(np.abs(d['acceleration']))
            ax.set_title(f"{st} - {c}\nPGA: {pga:.4f}", fontsize=9)
            ax.set_xlabel('Time (s)', fontsize=8)
            ax.set_ylabel('Acc', fontsize=8)
            ax.grid(True, alpha=0.3)
        
        loc = self.selected_earthquake['location']
        year = self.selected_earthquake['year']
        mag = self.selected_earthquake['magnitude']
        self.fig.suptitle(f"{loc} ({year}) M{mag}", fontsize=12, fontweight='bold')
        self.fig.tight_layout(rect=[0, 0, 1, 0.95])
        self.cv.draw()
    
    def _show_large_popup(self):
        if not self.selected_earthquake:
            messagebox.showwarning("Warning", "Select an earthquake first")
            return
        
        proc = self.selected_earthquake['processor']
        data = proc.get_data_by_station()
        info = {
            'location': self.selected_earthquake['location'],
            'year': self.selected_earthquake['year'],
            'magnitude': self.selected_earthquake['magnitude']
        }
        
        popup = LargePlotPopup(self.root, f"{info['location']} - All Stations")
        popup.set_data(data, info)
    
    def _save_csv(self):
        if not self.selected_earthquake:
            messagebox.showwarning("Warning", "Select an earthquake first")
            return
        
        folder = filedialog.askdirectory(title="Select folder to save CSV files")
        if not folder:
            return
        
        proc = self.selected_earthquake['processor']
        data = proc.get_data_by_station()
        info = {
            'location': self.selected_earthquake['location'],
            'year': self.selected_earthquake['year'],
            'magnitude': self.selected_earthquake['magnitude']
        }
        
        saved = 0
        for station, components in data.items():
            filename = f"{station}_M{info['magnitude']:.1f}.csv"
            filepath = os.path.join(folder, filename)
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                
                writer.writerow([
                    f"Station: {station}",
                    f"Earthquake: {info['location']}",
                    f"Year: {info['year']}",
                    f"Magnitude: {info['magnitude']:.1f}"
                ])
                
                writer.writerow(['Time(s)', 'EW_Acc', 'NS_Acc', 'V_Acc'])
                
                max_len = 0
                for comp, d in components.items():
                    max_len = max(max_len, len(d['time']))
                
                for i in range(max_len):
                    row = [f"{i * 0.005:.4f}"]
                    for comp in ['EW', 'NS', 'V']:
                        if comp in components and i < len(components[comp]['acceleration']):
                            row.append(f"{components[comp]['acceleration'][i]:.8f}")
                        else:
                            row.append('')
                    writer.writerow(row)
            
            saved += 1
        
        messagebox.showinfo("Saved", f"Saved {saved} CSV files\n{folder}")


from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

if __name__ == "__main__":
    root = tk.Tk()
    app = StationDataApp(root)
    root.mainloop()