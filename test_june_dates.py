import pandas as pd
import glob
files = glob.glob('data_history/*.csv') + glob.glob('data_history/*.xlsx') + glob.glob('data_history/*.xls')
dfs = []
for f in files:
    if '~$' in f: continue
    if f.endswith('.csv'): dfs.append(pd.read_csv(f, on_bad_lines='skip', low_memory=False))
    else: dfs.append(pd.read_excel(f, engine='openpyxl'))
if dfs:
    df = pd.concat(dfs, ignore_index=True)
    def clean_date(s):
        return s.astype(str).str.replace(r'^[=\"]+', '', regex=True).str.replace(r'[\"]+$', '', regex=True)
        
    s_audit = clean_date(df['审核时间'])
    s_dispatch = clean_date(df['发货时间']) if '发货时间' in df.columns else None
    
    # How app.py does it right now
    audit_dt = pd.to_datetime(s_audit, errors='coerce', format='mixed')
    
    if s_dispatch is not None:
        dispatch_dt_mixed = pd.to_datetime(s_dispatch, errors='coerce', format='mixed')
        dispatch_dt_nomixed = pd.to_datetime(s_dispatch, errors='coerce')
        
        # Look at June 2026 data based on audit time
        m_june = (audit_dt >= '2026-06-01') & (audit_dt < '2026-07-01')
        
        with open('june_dates_debug.txt', 'w', encoding='utf-8') as out:
            out.write(f"Total June rows: {m_june.sum()}\n")
            
            # Check how many have valid dispatch times
            valid_dispatch_mixed = dispatch_dt_mixed[m_june].notna().sum()
            valid_dispatch_nomixed = dispatch_dt_nomixed[m_june].notna().sum()
            
            out.write(f"Valid dispatch times in June (mixed): {valid_dispatch_mixed}\n")
            out.write(f"Valid dispatch times in June (nomixed): {valid_dispatch_nomixed}\n")
            
            # Sample raw dispatch strings for June that failed mixed
            failed_mixed_mask = m_june & dispatch_dt_mixed.isna()
            out.write("\nSample raw '发货时间' failing mixed parsing:\n")
            out.write(str(s_dispatch[failed_mixed_mask].head(20)))
            
            out.write("\n\nSample raw '发货时间' failing nomixed parsing:\n")
            failed_nomixed_mask = m_june & dispatch_dt_nomixed.isna()
            out.write(str(s_dispatch[failed_nomixed_mask].head(20)))
