import pandas as pd
df = pd.read_excel('data_inbound/26년 1월 입고 내역.xlsx')
with open('debug4.txt', 'w', encoding='utf-8') as f:
    for c in df.columns:
        try:
            total = pd.to_numeric(df[c].astype(str).str.replace('箱', ''), errors='coerce').sum()
            f.write(f"{c}: {total}\n")
        except:
            pass
