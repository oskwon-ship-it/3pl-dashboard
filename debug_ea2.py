import pandas as pd
import glob

with open('debug_ea2.txt', 'w', encoding='utf-8') as f:
    h_files = [x for x in glob.glob('data_history/*5*.xlsx') + glob.glob('data_history/*05*.xlsx') if '~$' not in x]
    if not h_files: h_files = [x for x in glob.glob('data_history/*.xlsx') if '~$' not in x]
    
    hdf_list = [pd.read_excel(file) for file in h_files]
    hdf = pd.concat(hdf_list, ignore_index=True) if hdf_list else pd.DataFrame()
    
    if not hdf.empty and '货主' in hdf.columns:
        ea_hdf = hdf[hdf['货主'] == 'EA']
        
        # 1. By 발송시간 (Dispatch Time)
        ea_hdf['发货时间'] = pd.to_datetime(ea_hdf['发货时间'], errors='coerce')
        ea_hdf['dispatch_month'] = ea_hdf['发货时间'].dt.month
        
        # 2. By 접수시간/심사시간 (Receive Time)
        ea_hdf['审核时间'] = pd.to_datetime(ea_hdf['审核时间'], errors='coerce')
        ea_hdf['receive_month'] = ea_hdf['审核时间'].dt.month
        
        f.write(f"EA 화주 - 발송시간(发货时间) 기준 5월 주문 수: {ea_hdf[ea_hdf['dispatch_month'] == 5]['出库单号'].nunique()}\n")
        f.write(f"EA 화주 - 심사시간(审核时间) 기준 5월 주문 수: {ea_hdf[ea_hdf['receive_month'] == 5]['出库单号'].nunique()}\n")
        
        # 3. What if we don't drop duplicates yet? Just row count?
        f.write(f"EA 화주 - 심사시간(审核时间) 기준 5월 행(Row) 수: {len(ea_hdf[ea_hdf['receive_month'] == 5])}\n")
