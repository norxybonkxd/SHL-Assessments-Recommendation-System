import pandas as pd

# Read train.csv
train = pd.read_csv('train.csv')

# Create submission.csv with Query and Assessment_url columns
submission = train[['Query', 'Assessment_url']].copy()

# Save to submission.csv
submission.to_csv('submission.csv', index=False)

print(f"* Generated submission.csv from train.csv")
print(f"* Total rows: {len(submission)}")
print(f"* Format: Query, Assessment_url")
print(f"\nFirst 10 rows:")
print(submission.head(10))
