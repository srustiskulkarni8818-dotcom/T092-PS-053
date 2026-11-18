from loaders import load_csv

sellers = load_csv("data/sellers.csv")
print("Number of sellers:", len(sellers))
print("First seller:", sellers[0])