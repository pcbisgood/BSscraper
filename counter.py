

import pandas as pd

# Leggi il file CSV
file_path = 'CSV/IT_elettricista_All_03-12-2024.csv'  # Sostituisci con il percorso corretto
df = pd.read_csv(file_path, sep=';')  # Cambia 'sep' in base al separatore usato nel file


# Conta i valori validi (non nulli e non vuoti) per ogni colonna
telefono_count = df['TELEFONO'].notnull().sum()
whatsapp_count = df['WHATSAPP'].notnull().sum()
email_count = df['EMAIL'].notnull().sum()

print(f"Numero totale di TELEFONO: {telefono_count}")
print(f"Numero totale di WHATSAPP: {whatsapp_count}")
print(f"Numero totale di EMAIL: {email_count}")
