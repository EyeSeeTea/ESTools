import json
delete_list=[]
# Abrimos el archivo .json y cargamos los datos en una variable
with open('normalprogram.json', 'r') as f:
    data = json.load(f)["events"]
    print(len(data))

    # Obtenemos los valores del diccionario y los almacenamos en una lista
    eventos =data

    # Separamos los eventos en listas de 250 elementos
    eventos_por_lista = [eventos[i:i + 5000] for i in range(0, len(eventos), 5000)]

    # Guardamos cada lista de eventos en un archivo .json separado
    for i, lista_eventos in enumerate(eventos_por_lista):
        nombre_archivo = f"eventos_{i}.json"
        with open(nombre_archivo, 'w') as f:
            json.dump({"events": lista_eventos}, f)