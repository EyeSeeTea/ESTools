import os
import requests
import json

# URL de destino para hacer la petición POST

#url = 'https://extranet.who.int/dhis2/api/38/tracker?async=false&skipRuleEngine=True'
url = 'http://localhost:8080/api/38/tracker?async=false'

# Credenciales para autenticación básica
username = ''
password = ''

# Obtener la lista de archivos .json del directorio actual
lista_archivos = [f for f in os.listdir('.') if f.endswith('.json')]

# Iterar sobre los archivos y hacer una petición POST con su contenido
for archivo in lista_archivos:
    # Abrir el archivo y cargar su contenido en un diccionario
    with open(archivo, 'r') as f:
        data = json.load(f)

        # Hacer la petición POST con el contenido del archivo y las credenciales de autenticación
        response = requests.post(url, json=data, auth=(username, password))
        for event in data["events"]:
            print("'"+event["id"]+"',")
        # Imprimir el resultado de la petición
        print(f"Archivo {archivo}: {response.status_code} {response.text}")
        print(f"continue")