# PESMOS Station GUI - FINAL VERSION

## Files
- `station_data_gui.py` - Station data viewer with scrollable popup
- `station_map_gui.py` - Station map with editable legend

## Features

### Station Data GUI
- Load earthquake zip files from PESMOS data folder
- View time history plots for EW, NS, V components
- Large scrollable popup to see all stations clearly
- **Save CSV per station** (e.g., `BAG_M4.5.csv`)
- **CSV format**: Row1=Station info, Row2=Headers (Time, EW_Acc, NS_Acc, V_Acc), Row3+=Data

### Station Map GUI  
- Earthquake source with distance circles (10-500 km)
- India/Nepal boundaries
- **Edit legend settings** - click "⚙️ Edit Legend" button
- **Click any text on map to edit** - font, bold, color, size popup
- Save map as PNG image

## Running
```bash
# Station Data GUI
python station_data_gui.py

# Station Map GUI  
python station_map_gui.py
```

Or use the batch file:
```
run_gui.bat
```

## CSV Output Format
Each station saved as `StationName_M4.5.csv`:
```
Station: BAG, Earthquake: Chamoli_1999, Year: 1999, Magnitude: 4.5
Time(s),EW_Acc,NS_Acc,V_Acc
0.0000,0.00000000,0.00000000,0.00000000
0.0050,0.00123456,0.00098765,0.00045678
...
```

## Fixes in This Version
1. ✅ Fixed CSV multi-column format (Time, EW, NS, V as columns)
2. ✅ Fixed infinite columns bug - now limited to 4 columns
3. ✅ Fixed legend editor numeric type conversion error
4. ✅ Added text editing popup (click text to edit font/color/size)