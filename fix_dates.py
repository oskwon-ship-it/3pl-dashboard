with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(len(lines)):
    if "pd.to_datetime" in lines[i] and "errors='coerce'" in lines[i] and "format='mixed'" not in lines[i]:
        lines[i] = lines[i].replace("errors='coerce'", "errors='coerce', format='mixed'")

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
