import pandas as pd
import glob

with open('debug_ea4.txt', 'w', encoding='utf-8') as f:
    d_files = [x for x in glob.glob('data_detailed/*5*.xlsx') + glob.glob('data_detailed/*05*.xlsx') if '~$' not in x]
    if not d_files: d_files = [x for x in glob.glob('data_detailed/*.xlsx') if '~$' not in x]
    df_list = [pd.read_excel(file) for file in d_files]
    df = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

    h_files = [x for x in glob.glob('data_history/*5*.xlsx') + glob.glob('data_history/*05*.xlsx') if '~$' not in x]
    if not h_files: h_files = [x for x in glob.glob('data_history/*.xlsx') if '~$' not in x]
    hdf_list = [pd.read_excel(file) for file in h_files]
    hist_df = pd.concat(hdf_list, ignore_index=True) if hdf_list else pd.DataFrame()
    
    if not df.empty and not hist_df.empty:
        # Replicate app.py merge logic
        hist_df_sub = hist_df.drop_duplicates(subset=['物流单号'])
        df = df.merge(hist_df_sub[['物流单号', '审核时间']], on='物流单号', how='left')
        df['审核时间'] = pd.to_datetime(df['审核时间'], errors='coerce')
        df['접수일자'] = df['审核时间'].dt.date
        
        # Filter for EA and May
        ea_df = df[df['货主'] == 'EA']
        ea_df_may = ea_df[ea_df['审核时间'].dt.month == 5]
        
        f.write(f"Dashboard Data (df) - EA May Orders (出库单号 nunique): {ea_df_may['出库单号'].nunique()}\n")
        f.write(f"Dashboard Data (df) - EA May Rows: {len(ea_df_may)}\n")
        
        # Now check raw hist_df for EA May
        ea_hist = hist_df[hist_df['货主'] == 'EA']
        ea_hist['审核时间'] = pd.to_datetime(ea_hist['审核时间'], errors='coerce')
        ea_hist_may = ea_hist[ea_hist['审核时间'].dt.month == 5]
        
        f.write(f"History Data (hist_df) - EA May Orders (出库单号 nunique): {ea_hist_may['出库单号'].nunique()}\n")
        f.write(f"History Data (hist_df) - EA May Rows: {len(ea_hist_may)}\n")
        
        missing_orders = set(ea_hist_may['出库单号'].dropna()) - set(ea_df_may['出库单号'].dropna())
        f.write(f"\nMissing Orders in Detailed (present in History, but not in Detailed): {len(missing_orders)}\n")
        if missing_orders:
            f.write(f"Sample Missing Orders: {list(missing_orders)[:5]}\n")
            
        f.write(f"\nWait, what if they were excluded because their 物流单号 didn't match?\n")
        ea_df_unfiltered = ea_df
        f.write(f"Total EA orders in Detailed (all months): {ea_df_unfiltered['出库单号'].nunique()}\n")
