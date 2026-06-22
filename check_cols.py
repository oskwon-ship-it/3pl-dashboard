import pandas as pd
import glob
with open('cols.txt', 'w', encoding='utf-8') as f:
    files2 = glob.glob('data_detailed/*.xlsx')
    if files2:
        df2 = pd.read_excel(files2[0])
        f.write("Columns: " + ", ".join(df2.columns.tolist()) + "\n")
