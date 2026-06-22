import os

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Glob replacements
glob_replacements = {
    'glob.glob("data_detailed/*.xlsx") + glob.glob("data_detailed/*.xls")': 'glob.glob("data_detailed/*.csv") + glob.glob("data_detailed/*.xlsx") + glob.glob("data_detailed/*.xls")',
    'glob.glob("data_history/*.xlsx") + glob.glob("data_history/*.xls")': 'glob.glob("data_history/*.csv") + glob.glob("data_history/*.xlsx") + glob.glob("data_history/*.xls")',
    'glob.glob(os.path.join("data_inbound", "*.xlsx"))': 'glob.glob(os.path.join("data_inbound", "*.csv")) + glob.glob(os.path.join("data_inbound", "*.xlsx"))',
    'glob.glob("data_outbound_cj/*.xlsx") + glob.glob("data_outbound_cj/*.xls")': 'glob.glob("data_outbound_cj/*.csv") + glob.glob("data_outbound_cj/*.xlsx") + glob.glob("data_outbound_cj/*.xls")',
    'glob.glob("data_outbound_quick/*.xlsx") + glob.glob("data_outbound_quick/*.xls")': 'glob.glob("data_outbound_quick/*.csv") + glob.glob("data_outbound_quick/*.xlsx") + glob.glob("data_outbound_quick/*.xls")'
}

for old, new in glob_replacements.items():
    code = code.replace(old, new)

# 2. History loop replacement
old_hist = """        try:
            engine = 'openpyxl' if file.endswith('.xlsx') else None
            temp_df = pd.read_excel(file, usecols=col_filter, engine=engine)
            history_list.append(temp_df)
        except Exception as e:"""
new_hist = """        try:
            if not file.endswith('.csv'):
                csv_file = os.path.splitext(file)[0] + '.csv'
                if os.path.exists(csv_file): continue
            
            if file.endswith('.csv'):
                temp_df = pd.read_csv(file, usecols=lambda c: c in use_cols)
            else:
                engine = 'openpyxl' if file.endswith('.xlsx') else None
                temp_df = pd.read_excel(file, usecols=col_filter, engine=engine)
            history_list.append(temp_df)
        except Exception as e:"""
code = code.replace(old_hist, new_hist)

# 3. Detailed loop replacement
old_det = """        try:
            engine = 'openpyxl' if file.endswith('.xlsx') else None
            temp_df = pd.read_excel(file, usecols=col_filter, engine=engine)
            df_list.append(temp_df)
        except Exception as e:"""
new_det = """        try:
            if not file.endswith('.csv'):
                csv_file = os.path.splitext(file)[0] + '.csv'
                if os.path.exists(csv_file): continue
            
            if file.endswith('.csv'):
                temp_df = pd.read_csv(file, usecols=lambda c: c in use_cols)
            else:
                engine = 'openpyxl' if file.endswith('.xlsx') else None
                temp_df = pd.read_excel(file, usecols=col_filter, engine=engine)
            df_list.append(temp_df)
        except Exception as e:"""
code = code.replace(old_det, new_det)

# 4. Inbound loop replacement
old_inb = """        try:
            engine = 'openpyxl' if file.endswith('.xlsx') else None
            temp_df = pd.read_excel(file, engine=engine)
            temp_df = temp_df[[c for c in col_filter if c in temp_df.columns]]"""
new_inb = """        try:
            if not file.endswith('.csv'):
                csv_file = os.path.splitext(file)[0] + '.csv'
                if os.path.exists(csv_file): continue
                
            if file.endswith('.csv'):
                temp_df = pd.read_csv(file)
            else:
                engine = 'openpyxl' if file.endswith('.xlsx') else None
                temp_df = pd.read_excel(file, engine=engine)
            temp_df = temp_df[[c for c in col_filter if c in temp_df.columns]]"""
code = code.replace(old_inb, new_inb)

# 5. CJ loop replacement
old_cj = """        try:
            temp_df = pd.read_excel(file, engine='openpyxl' if file.endswith('.xlsx') else None)
            cj_list.append(temp_df)
        except: pass"""
new_cj = """        try:
            if not file.endswith('.csv'):
                csv_file = os.path.splitext(file)[0] + '.csv'
                if os.path.exists(csv_file): continue
                
            if file.endswith('.csv'):
                temp_df = pd.read_csv(file)
            else:
                temp_df = pd.read_excel(file, engine='openpyxl' if file.endswith('.xlsx') else None)
            cj_list.append(temp_df)
        except: pass"""
code = code.replace(old_cj, new_cj)

# 6. Quick loop replacement
old_qk = """        try:
            temp_df = pd.read_excel(file, engine='openpyxl' if file.endswith('.xlsx') else None)
            qk_list.append(temp_df)
        except: pass"""
new_qk = """        try:
            if not file.endswith('.csv'):
                csv_file = os.path.splitext(file)[0] + '.csv'
                if os.path.exists(csv_file): continue
                
            if file.endswith('.csv'):
                temp_df = pd.read_csv(file)
            else:
                temp_df = pd.read_excel(file, engine='openpyxl' if file.endswith('.xlsx') else None)
            qk_list.append(temp_df)
        except: pass"""
code = code.replace(old_qk, new_qk)

# 7. Add os if missing
if 'import os' not in code:
    code = 'import os\n' + code

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("done")
