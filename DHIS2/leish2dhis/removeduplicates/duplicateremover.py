import json
delete_list=[]
# Abrimos el archivo .json y cargamos los datos en una variable
mappedEventLists= dict()
listofevents = list()
with open('curlrareprogram.json', 'r') as f:
    data = json.load(f)["events"]
    print(len(data))

    # Obtenemos los valores del diccionario y los almacenamos en una lista
    eventos =data
    for evento in eventos:
        dataValue = evento["dataValues"][0]
        dataElement = dataValue["dataElement"] + str(dataValue["value"])
        mappedEventLists[evento["orgUnit"]+evento["program"]+evento["programStage"]+evento["eventDate"]+dataElement]=True
        listofevents.append(evento)
    # Separamos los eventos en listas de 250 elementos

    with open('curlrareprogram2.json', 'r') as f2:
        data2 = json.load(f2)["events"]
        eventos =data2

        for evento in eventos:
            dataValue = evento["dataValues"][0]
            dataElement = dataValue["dataElement"] + str(dataValue["value"])
            if evento["orgUnit"] + evento["program"] + evento["programStage"] + evento["eventDate"] + dataElement not in mappedEventLists.keys():
                listofevents.append(evento)
with open("output.json", 'w') as f:
    json.dump({"events": listofevents}, f, indent=4)