#!/usr/bin/env python3
"""
Station Data GUI - PESMOS Earthquake Records Viewer (ENHANCED)
- All stations & components saved in CSV
- Large popup plots with save options
- Editable plot settings
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

# ═══════════════════════════════════════════════════════════════════════════════
# DATA PROCESSOR
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
            
            # Try to get magnitude from filename
            mag_match = re.search(r'M-?(\d+\.?\d*)', basename, re.IGNORECASE)
            if mag_match:
                self.metadata['magnitude'] = float(mag_match.group(1))
            else:
                self.metadata['magnitude'] = 4.5  # Default
    
    def _parse_file(self, content, filename):
        lines = content.strip().split('\n')
        metadata = {}
        data_lines = []
        
        for line in lines[:30]:
            line = line.strip()
            
            match = re.search(r'Station\s*:\s*(\w+)', line, re.IGNORECASE)
            if match:
                metadata['station'] = match.group(1)
            
            match = re.search(r'Mag[nitude]*\s*[:=]\s*(\d+\.?\d*)', line, re.IGNORECASE)
            if match:
                metadata['magnitude'] = float(match.group(1))
            
            if filename.endswith('.ew'):
                metadata['component'] = 'EW'
                metadata['direction'] = 'East-West'
            elif filename.endswith('.ns'):
                metadata['component'] = 'NS'
                metadata['direction'] = 'North-South'
            elif filename.endswith('.vt'):
                metadata['component'] = 'Vertical'
                metadata['direction'] = 'Vertical'
        
        for line in lines[30:]:
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
        for name in self.files_data.keys():
            parts = name.split('/')
            if len(parts) >= 3:
                station_code = parts[2].split('_')[0]
                stations.add(station_code)
        
        max_pga = 0
        for name, data in self.files_data.items():
            pga = np.max(np.abs(data['acceleration']))
            if pga > max_pga:
                max_pga = pga
        
        return {
            'year': self.metadata.get('year', 2000),
            'location': self.metadata.get('earthquake', 'Unknown'),
            'magnitude': self.metadata.get('magnitude', 4.5),
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
        """Get all data for CSV export"""
        all_data = []
        for name, data in self.files_data.items():
            parts = name.split('/')
            station = parts[2].split('_')[0] if len(parts) >= 3 else 'Unknown'
            component = data.get('metadata', {}).get('component', 'Unknown')
            
            for t, a in zip(data['time'], data['acceleration']):
                all_data.append({
                    'station': station,
                    'component': component,
                    'time': t,
                    'acceleration': a
                })
        return all_data


# ═══════════════════════════════════════════════════════════════════════════════
# POPUP PLOT WINDOW
# ═══════════════════════════════════════════════════════════════════════════════
class PlotPopup(tk.Toplevel):
    def __init__(self, parent, title, fig):
        super().__init__(parent)
        self.title(title)
        self.geometry("1200x700")
        self.configure(bg='#1E2A3A')
        
        self.fig = fig
        
        # Controls
        ctl = tk.Frame(self, bg='#1E2A3A')
        ctl.pack(fill=tk.X, padx=4, pady=4)
        
        tk.Button(ctl, text="💾 Save Image", command=self._save_image,
                  bg='#8E44AD', fg='white', font=('Helvetica',10), padx=10).pack(side=tk.RIGHT, padx=4)
        tk.Button(ctl, text="💾 Save CSV", command=self._save_csv,
                  bg='#1565C0', fg='white', font=('Helvetica',10), padx=10).pack(side=tk.RIGHT, padx=4)
        
        # Canvas
        self.cv = FigureCanvasTkAgg(self.fig, master=self)
        self.cv.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        toolbar = tk.Frame(self, bg='#1E2A3A')
        toolbar.pack(fill=tk.X)
        NavigationToolbar2Tk(self.cv, toolbar)
        
        self.data_to_save = None
    
    def set_csv_data(self, data):
        self.data_to_save = data
    
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
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['station', 'component', 'time', 'acceleration'])
            writer.writeheader()
            writer.writerows(self.data_to_save)
        
        messagebox.showinfo("Saved", f"Data saved to {filepath}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════
class StationDataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PESMOS Earthquake Station Records - Enhanced")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2C3E50')
        
        self.data_dir = None
        self.earthquake_data = []
        self.selected_earthquake = None
        
        self._build_ui()
    
    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#1A3A5C', height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="PESMOS Earthquake Station Records Database (Enhanced)",
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
        
        # Search
        search_frame = tk.Frame(left_panel, bg='#1E2A3A')
        search_frame.pack(fill=tk.X, padx=8, pady=4)
        tk.Label(search_frame, text="🔍", bg='#1E2A3A', fg='white').pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._filter_list)
        tk.Entry(search_frame, textvariable=self.search_var, bg='#0D1B2A', fg='#E3F2FD',
                 font=('Courier',9), width=25).pack(side=tk.LEFT, padx=4)
        
        # Earthquake list
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
        
        tk.Button(btn_frame, text="💾 Save All CSV", command=self._save_all_csv,
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
        """Show large popup plot"""
        if not self.selected_earthquake:
            messagebox.showwarning("No Data", "Select an earthquake first")
            return
        
        processor = self.selected_earthquake['processor']
        
        # Create large figure
        fig = Figure(figsize=(16, 10), facecolor='white')
        
        files_to_plot = list(processor.files_data.items())
        n = len(files_to_plot)
        
        if n == 0:
            messagebox.showwarning("No Data", "No data available")
            return
        
        rows = (n + 2) // 3
        for i, (name, data) in enumerate(files_to_plot):
            ax = fig.add_subplot(rows, 3, i+1)
            
            time = data['time']
            acc = data['acceleration']
            pga = np.max(np.abs(acc))
            
            ax.plot(time, acc, 'b-', lw=1.0)
            ax.fill_between(time, acc, alpha=0.3, color='blue')
            ax.set_xlabel('Time (s)', fontsize=9)
            ax.set_ylabel('Acceleration (m/s²)', fontsize=9)
            
            parts = name.split('/')
            station = parts[2].split('_')[0] if len(parts) >= 3 else 'Unknown'
            component = data.get('metadata', {}).get('component', 'Unknown')
            ax.set_title(f"{station} - {component} | PGA: {pga:.4f} m/s²", fontsize=10, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend([f"Max: {pga:.4f}"], loc='upper right', fontsize=7)
        
        eq_name = self.selected_earthquake['location']
        year = self.selected_earthquake['year']
        mag = self.selected_earthquake['magnitude']
        fig.suptitle(f"Earthquake: {eq_name} ({year}) | Magnitude: M{mag}\nAll Stations & Components",
                     fontsize=14, fontweight='bold')
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Create popup
        popup = PlotPopup(self.root, f"{eq_name} - All Time Histories", fig)
        
        # Prepare CSV data
        all_data = processor.get_all_data_for_csv()
        popup.set_csv_data(all_data)
    
    def _save_all_csv(self):
        """Save all displayed data to CSV"""
        if not self.selected_earthquake:
            messagebox.showwarning("No Data", "Select an earthquake first")
            return
        
        filepath = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV", "*.csv")])
        if not filepath:
            return
        
        processor = self.selected_earthquake['processor']
        all_data = processor.get_all_data_for_csv()
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['station', 'component', 'time', 'acceleration'])
            writer.writeheader()
            writer.writerows(all_data)
        
        messagebox.showinfo("Saved", f"All data saved to {filepath}\nTotal records: {len(all_data)}")
    
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