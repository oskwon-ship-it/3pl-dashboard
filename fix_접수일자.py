with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_line_203 = "hist_df['접수일자'] = pd.to_datetime(hist_df['审核时间'], errors='coerce', format='mixed').dt.date"
new_line_203 = "hist_df['접수일자'] = hist_df['접수시간'].dt.date"

old_line_211 = "detail_df['접수일자'] = pd.to_datetime(detail_df['审核时间'], errors='coerce', format='mixed').dt.date"
new_line_211 = "detail_df['접수일자'] = detail_df['접수시간'].dt.date"

content = content.replace(old_line_203, new_line_203)
content = content.replace(old_line_211, new_line_211)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fix applied.")
