import pandas as pd
import glob

with open('debug_may.txt', 'w', encoding='utf-8') as f:
    files = glob.glob('data_detailed/*05*.xlsx') + glob.glob('data_detailed/*5月*.xlsx')
    if not files:
        files = glob.glob('data_detailed/*.xlsx') # fallback but we want May
    
    df_list = []
    for file in files:
        if '5' in file or '05' in file:
            df_list.append(pd.read_excel(file))
            
    if df_list:
        df = pd.concat(df_list, ignore_index=True)
        
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
            f.write(f"\nMay Data - Number of Next-Day Dispatches: {len(failures)}\n")
            if not failures.empty:
                f.write(failures[['审核时间', '发货时间']].head(20).to_string() + "\n")
