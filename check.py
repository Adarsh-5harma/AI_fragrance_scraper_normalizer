import csv

with open('data/master_catalog.csv') as f:
    rows = list(csv.DictReader(f))

check_words = ['men', 'woman', 'boy', 'girl', 'homme', 'femme', 'mujer', 'hombre']

print('Products with gender words but still Unknown:')
print('-' * 60)
for r in rows:
    name   = r['product_name'].lower()
    gender = r['gender']
    for w in check_words:
        if w in name and gender == 'Unknown':
            print(f'[{w}]  {r["product_name"]}')
            break

print()
print('All Unknown products:')
print('-' * 60)
for r in rows:
    if r['gender'] == 'Unknown':
        print(r['product_name'])