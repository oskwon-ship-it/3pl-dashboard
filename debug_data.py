import pandas as pd
import glob

with open('debug_output.txt', 'w', encoding='utf-8') as f:
    files = glob.glob('data_detailed/*5*.xlsx') + glob.glob('data_detailed/*5*.xls') + glob.glob('data_detailed/*05*.xlsx')
    if not files:
        files = glob.glob('data_detailed/*.xlsx')
        
    df = pd.read_excel(files[0])
    
    # Status columns check
    status_cols = [c for c in df.columns if '状态' in c]
    f.write(f"Status Columns: {status_cols}\n")
    for c in status_cols:
        f.write(f"{c}: {df[c].unique().tolist()}\n")
        
    # Merge with history
    h_files = glob.glob('data_history/*.xlsx')
    if h_files:
        hdf = pd.read_excel(h_files[0])
        hdf = hdf.drop_duplicates(subset=['物流单号'])
        df = df.merge(hdf[['物流单号', '审核时间']], on='物流单号', how='left')
        
        df['审核时间'] = pd.to_datetime(df['审核时间'], errors='coerce')
        df['发货时间'] = pd.to_datetime(df['发货时间'], errors='coerce')
        
        df['접수일자'] = df['审核时间'].dt.date
        df['发货일자'] = df['发货时间'].dt.date
        
        failures = df[df['发货일자'] > df['접수일자']]
        f.write(f"\nNumber of Next-Day Dispatches: {len(failures)}\n")
        if not failures.empty:
            f.write("Sample Next-Day Dispatches (Receive vs Dispatch):\n")
            f.write(failures[['审核时间', '发货时间']].head(10).to_string() + "\n")
