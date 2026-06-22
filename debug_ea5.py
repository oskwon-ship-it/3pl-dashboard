import pandas as pd
import glob

with open('debug_ea5.txt', 'w', encoding='utf-8') as f:
    # Load History
    h_files = [x for x in glob.glob('data_history/*5*.xlsx') + glob.glob('data_history/*05*.xlsx') if '~$' not in x]
    if not h_files: h_files = [x for x in glob.glob('data_history/*.xlsx') if '~$' not in x]
    hdf_list = [pd.read_excel(file) for file in h_files]
    hist_df = pd.concat(hdf_list, ignore_index=True) if hdf_list else pd.DataFrame()

    # Load Detailed
    d_files = [x for x in glob.glob('data_detailed/*5*.xlsx') + glob.glob('data_detailed/*05*.xlsx') if '~$' not in x]
    if not d_files: d_files = [x for x in glob.glob('data_detailed/*.xlsx') if '~$' not in x]
    df_list = [pd.read_excel(file) for file in d_files]
    df = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

    # Filter EA
    hist_ea = hist_df[hist_df['货主'] == 'EA']
    df_ea = df[df['货主'] == 'EA']

    # Convert Audit Time in History
    hist_ea['审核时间'] = pd.to_datetime(hist_ea['审核时间'], errors='coerce')
    hist_ea_may = hist_ea[hist_ea['审核时间'].dt.month == 5]
    
    may_orders_in_hist = set(hist_ea_may['出库单号'].dropna())
    f.write(f"History May Orders: {len(may_orders_in_hist)}\n")
    
    # Are these orders in Detailed?
    all_orders_in_detailed = set(df_ea['出库单号'].dropna())
    f.write(f"Detailed Total Orders (All Months): {len(all_orders_in_detailed)}\n")
    
    missing_from_detailed = may_orders_in_hist - all_orders_in_detailed
    f.write(f"Orders in History May, but completely MISSING from Detailed files: {len(missing_from_detailed)}\n")
    
    if len(missing_from_detailed) > 0:
        f.write(f"Sample Missing Orders: {list(missing_from_detailed)[:5]}\n")
    else:
        # If they ARE in detailed, why did merge fail?
        # Let's check matching of 物流单号
        f.write("All May orders from History are present in Detailed.\n")
        # Let's check if the 物流单号 matches between Detailed and History for these 249
        hist_missing = hist_ea_may[~hist_ea_may['出库单号'].isin(df_ea['出库单号'])]
