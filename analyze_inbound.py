import pandas as pd
import glob
import json

inbound_files = glob.glob("data_inbound/*.xlsx") + glob.glob("data_inbound/*.xls")
inbound_files = [f for f in inbound_files if "~$" not in f]

schema_info = {}

for file in inbound_files:
    try:
        df = pd.read_excel(file)
        schema_info[file] = {
            "columns": list(df.columns),
            "sample": df.head(3).to_dict(orient="records"),
            "row_count": len(df)
        }
    except Exception as e:
        schema_info[file] = {"error": str(e)}

with open('inbound_schema.json', 'w', encoding='utf-8') as f:
    json.dump(schema_info, f, ensure_ascii=False, indent=2)

print(f"Analyzed {len(inbound_files)} files.")
