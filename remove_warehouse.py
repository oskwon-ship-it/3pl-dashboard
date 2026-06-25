import sys

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if 'inv_files =' in line and 'data_inventory' in line:
        continue
        
    if '# 6. 재고 현황(Inventory) 로드' in line:
        skip = True
    if skip and 'return hist_df' in line:
        skip = False

    if not skip:
        if 'return hist_df, detail_df, in_df, cj_df, qk_df, misship_df, inv_df' in line:
            line = line.replace(', inv_df', '')
        if 'hist_df, detail_df, in_df, cj_df, qk_df, misship_df, inv_df = load_data' in line:
            line = line.replace(', inv_df', '')
            
        new_lines.append(line)

final_lines = []
skip_ui = False
for i, line in enumerate(new_lines):
    if 'st.markdown("### 📦 창고 로케이션 및 재고 현황")' in line:
        if final_lines and 'st.divider()' in final_lines[-1]:
            final_lines.pop()
        skip_ui = True
        
    if skip_ui and 'st.info("data_inventory 폴더에 재고 현황 데이터 파일이 없습니다.")' in line:
        skip_ui = False
        continue
        
    if not skip_ui:
        final_lines.append(line)

# Wait, st.stop() might be remaining! I should also remove the stray st.stop() if it's there.
# Let's just output the final lines.
with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(final_lines)

print('Successfully removed warehouse location logic.')
