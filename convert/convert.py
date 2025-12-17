import pandas as pd

# Path to your Excel file
file_path = "Gen_AI_Dataset.xlsx"

# Load Excel file
xls = pd.ExcelFile(file_path)

# Read sheets (change names if needed)
train_df = pd.read_excel(xls, sheet_name=0)  # first sheet
test_df  = pd.read_excel(xls, sheet_name=1)  # second sheet

# Save as CSV
train_df.to_csv("train.csv", index=False)
test_df.to_csv("test.csv", index=False)

print("✅ Conversion complete: train.csv and test.csv created")
