import re
import json

# Pedir al usuario que introduzca una fecha para filtrar
fecha = input("Por favor, introduzca una fecha en formato AAAA-MM-DD: ")
#
# Validar que la fecha ingresada tenga el formato correcto
if fecha != "":
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', fecha):
        print("Fecha no válida. Por favor, introduzca una fecha en formato AAAA-MM-DD.")
        exit()
# Pedir al usuario que introduzca un tipo de auditScope (opcional)
audit_scope = input("Introduce el tipo de auditScope (opcional, presiona Enter para omitir): ")

# Pedir al usuario que introduzca un valor para klass (opcional)
klass_prefix = input("Introduce el valor inicial para 'klass' (opcional, presiona Enter para omitir): ")

# Pedir al usuario el nombre del usuario creado por (createdBy)
created_by = input("Introduce el nombre del usuario de 'createdBy' (opcional, presiona Enter para omitir): ")
# Abrir y leer el archivo unificado
try:
    with open("unified_logs.log", "r", encoding="utf-8") as infile, open(f"filtered_logs_{fecha}_{audit_scope if audit_scope else 'ALL'}_{klass_prefix if klass_prefix else 'ALL'}_{created_by if created_by else 'ALL'}.json", "w", encoding="utf-8") as outfile:

        outfile.write('{"audit":[')
        first_line_written = False
        # Iterar sobre cada línea en el archivo unificado
        for line in infile:
            # Verificar si la línea contiene la fecha ingresada
            if line.startswith(f"* INFO  {fecha}"):
                # Obtener la parte JSON de la línea
                json_part = re.search(r'{.*}', line)
                if json_part:
                    json_data = json.loads(json_part.group())
                    # Verificar si la línea coincide con todos los criterios ingresados
                    if (not audit_scope or json_data.get('auditScope') == audit_scope.upper()) and \
                       (not klass_prefix or json_data.get('klass', '').startswith(klass_prefix)) and \
                       (not fecha or json_data.get('createdAt', '').startswith(fecha)) and \
                       (not created_by or json_data.get('createdBy') == created_by):
                        processed_line = ('' if not first_line_written else ',') + re.sub(r'^[^{]+', '', line).rstrip()
                        # Escribir la línea procesada en el archivo de salida
                        outfile.write(processed_line)
                        first_line_written = True  # Actualizar la variable de control
        #outfile.seek(outfile.tell() - 1, 0)
        # Sobrescribir la última coma con ]}
        outfile.write(']}')

    # Informar al usuario que el proceso ha concluido
    print(f"Las líneas con fecha {fecha}{' y auditScope ' + audit_scope if audit_scope else ''}{' y klass que comienza con ' + klass_prefix if klass_prefix else ''}{' y createdBy ' + created_by if created_by else ''} han sido filtradas y guardadas en filtered_logs_{fecha}_{audit_scope if audit_scope else 'ALL'}_{klass_prefix if klass_prefix else 'ALL'}_{created_by if created_by else 'ALL'}.log")

except FileNotFoundError:
    print("Archivo unified_logs.log no encontrado.")
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")