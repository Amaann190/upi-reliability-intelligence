
import pandas as pd

# Step 1: Read the CSV file
df = pd.read_csv("data/raw/Remitter_Banks.csv")

# Step 2: Count the rows and columns
print("=== DATASET SIZE ===")
print("Number of rows:", df.shape[0])
print("Number of columns:", df.shape[1])

# Step 3: Display column names
print("\n=== COLUMN NAMES ===")
print(df.columns.tolist())

# Step 4: Display the first five rows
print("\n=== FIRST FIVE ROWS ===")
print(df.head().to_string(index=False))

# Step 5: Check data types
print("\n=== DATA TYPES ===")
print(df.dtypes)

# Step 6: Check for missing values
print("\n=== MISSING VALUES ===")
print(df.isnull().sum())

# Step 7: Check for duplicate rows
print("\n=== DUPLICATE ROWS ===")
print(df.duplicated().sum())