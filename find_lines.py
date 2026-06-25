with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
with open('found.txt', 'w', encoding='utf-8') as f2:
    for i, line in enumerate(lines):
        if 'inv_use_cols =' in line or 'st.markdown("### 📦 재고 현황 데이터")' in line:
            f2.write(f'{i}: {line.strip()}\n')
