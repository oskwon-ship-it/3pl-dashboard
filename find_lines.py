with open('app.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'date_range = st.date_input(' in line or 'st.markdown("#### 🔄 재고 회전율 분석' in line or 'if isinstance(date_range, tuple) and len(date_range) == 2:' in line:
            print(f'{i}: {line.strip()}')
