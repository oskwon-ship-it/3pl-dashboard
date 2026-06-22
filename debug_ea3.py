import pandas as pd
import glob

with open('debug_ea3.txt', 'w', encoding='utf-8') as f:
    h_files = [x for x in glob.glob('data_history/*5*.xlsx') + glob.glob('data_history/*05*.xlsx') if '~$' not in x]
    if not h_files: h_files = [x for x in glob.glob('data_history/*.xlsx') if '~$' not in x]
    
    hdf = pd.concat([pd.read_excel(file) for file in h_files], ignore_index=True) if h_files else pd.DataFrame()
    
    d_files = [x for x in glob.glob('data_detailed/*5*.xlsx') + glob.glob('data_detailed/*05*.xlsx') if '~$' not in x]
    if not d_files: d_files = [x for x in glob.glob('data_detailed/*.xlsx') if '~$' not in x]
    
    ddf = pd.concat([pd.read_excel(file) for file in d_files], ignore_index=True) if d_files else pd.DataFrame()
    
    ea_hdf = hdf[hdf['货主'] == 'EA'] if not hdf.empty and '货主' in hdf.columns else pd.DataFrame()
    ea_ddf = ddf[ddf['货主'] == 'EA'] if not ddf.empty and '货主' in ddf.columns else pd.DataFrame()
    
    if not ea_hdf.empty and not ea_ddf.empty:
        ea_hdf['审核时间'] = pd.to_datetime(ea_hdf['审核时间'], errors='coerce')
        ea_hdf_may = ea_hdf[ea_hdf['审核时间'].dt.month == 5]
        
        may_history_orders = set(ea_hdf_may['物流单号'].dropna())
        detailed_orders = set(ea_ddf['物流单号'].dropna())
        
        missing_orders = may_history_orders - detailed_orders
        
        f.write(f"May Audit Orders in History: {len(may_history_orders)}\n")
        f.write(f"Total Orders in Detailed: {len(detailed_orders)}\n")
        f.write(f"Missing Orders (in History May, but NOT in Detailed): {len(missing_orders)}\n")
        
        if missing_orders:
            sample_missing = list(missing_orders)[:5]
            f.write(f"Sample Missing 物流单号: {sample_missing}\n")
            # Let's see what happened to these in History
            missing_hdf = ea_hdf[ea_hdf['物流单号'].isin(sample_missing)]
            f.write("Their status in History file:\n")
            f.write(missing_hdf[['物流单号', '审核时间', '发货时间', '出库单状态']].to_string() + "\n")
