import pandas as pd
import glob

with open('debug_ea.txt', 'w', encoding='utf-8') as f:
    # 1. Load history files (출고 내역)
    h_files = [x for x in glob.glob('data_history/*5*.xlsx') + glob.glob('data_history/*05*.xlsx') if '~$' not in x]
    if not h_files: h_files = [x for x in glob.glob('data_history/*.xlsx') if '~$' not in x]
    
    hdf_list = [pd.read_excel(file) for file in h_files]
    hdf = pd.concat(hdf_list, ignore_index=True) if hdf_list else pd.DataFrame()
    
    # 2. Load detailed files (상세 출고 내역)
    d_files = [x for x in glob.glob('data_detailed/*5*.xlsx') + glob.glob('data_detailed/*05*.xlsx') if '~$' not in x]
    if not d_files: d_files = [x for x in glob.glob('data_detailed/*.xlsx') if '~$' not in x]
    
    ddf_list = [pd.read_excel(file) for file in d_files]
    ddf = pd.concat(ddf_list, ignore_index=True) if ddf_list else pd.DataFrame()
    
    f.write("=== EA 화주 분석 ===\n")
    if not hdf.empty and '货主' in hdf.columns:
        ea_hdf = hdf[hdf['货主'] == 'EA']
        f.write(f"출고 내역(History) EA 화주 전체 행(Row) 수: {len(ea_hdf)}\n")
        f.write(f"출고 내역(History) EA 화주 유효 주문(出库单号) 수: {ea_hdf['出库单号'].nunique() if '出库单号' in ea_hdf.columns else 'N/A'}\n")
    else:
        f.write("출고 내역 파일에 EA 화주 데이터가 없거나 货主 컬럼이 없습니다.\n")
        
    if not ddf.empty and '货主' in ddf.columns:
        ea_ddf = ddf[ddf['货主'] == 'EA']
        f.write(f"상세 출고(Detailed) EA 화주 전체 행(Row) 수: {len(ea_ddf)}\n")
        f.write(f"상세 출고(Detailed) EA 화주 유효 주문(出库单号) 수: {ea_ddf['出库单号'].nunique() if '出库单号' in ea_ddf.columns else 'N/A'}\n")
    else:
        f.write("상세 출고 파일에 EA 화주 데이터가 없거나 货主 컬럼이 없습니다.\n")
        
    # Check date ranges
    if not ea_ddf.empty and '发货时间' in ea_ddf.columns:
        ea_ddf['发货时间'] = pd.to_datetime(ea_ddf['发货时间'], errors='coerce')
        ea_ddf['month'] = ea_ddf['发货时间'].dt.month
        f.write(f"\n상세 출고(Detailed) 월별 유효 주문 수:\n{ea_ddf.groupby('month')['出库单号'].nunique()}\n")
        
    if not ea_hdf.empty and '发货时间' in ea_hdf.columns:
        ea_hdf['发货时间'] = pd.to_datetime(ea_hdf['发货时间'], errors='coerce')
        ea_hdf['month'] = ea_hdf['发货时间'].dt.month
        f.write(f"\n출고 내역(History) 월별 유효 주문 수:\n{ea_hdf.groupby('month')['出库单号'].nunique()}\n")
