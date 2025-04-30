import json
import random
from faker import Faker
from datetime import datetime, timedelta
from bson import ObjectId

fake = Faker()

def generar_usuarios(n=1000):
    return [{
        "_id": ObjectId(),
        "nombre": fake.name(),
        "correo": fake.email(),
        "telefono": fake.phone_number(),
        "direccion": {
            "calle": fake.street_name(),
            "zona": random.randint(1, 25),
            "ciudad": "Guatemala"
        },
        "tipo": random.choice(["cliente", "repartidor", "administrador"])
    } for _ in range(n)]

def generar_restaurantes(n=100):
    return [{
        "_id": ObjectId(),
        "nombre": fake.company(),
        "direccion": {
            "calle": fake.street_name(),
            "zona": random.randint(1, 25),
            "coordenadas": {
                "type": "Point",
                "coordinates": [round(random.uniform(-91, -90), 4), round(random.uniform(14, 15), 4)]
            }
        },
        "categorias": random.sample(["Pizza", "Italiana", "Mexicana", "China", "Vegana"], 2),
        "menu": [],
        "calificacionPromedio": round(random.uniform(3, 5), 1),
        "resenias": []
    } for _ in range(n)]

def generar_articulos(restaurantes, n_por_rest=10):
    articulos = []
    for r in restaurantes:
        for _ in range(n_por_rest):
            articulos.append({
                "_id": ObjectId(),
                "restaurante_id": r["_id"],
                "nombre": fake.word().capitalize(),
                "descripcion": fake.text(max_nb_chars=50),
                "categorias": random.sample(["pizza", "combo", "ensalada", "descuento"], 2),
                "precio": round(random.uniform(25, 100), 2),
                "disponible": random.choice([True, False]),
                "imagenes": []
            })
    return articulos

def generar_ordenes(usuarios, restaurantes, articulos, total=50000):
    ordenes = []
    for _ in range(total):
        user = random.choice(usuarios)
        rest = random.choice(restaurantes)
        items = []
        total_price = 0
        for _ in range(random.randint(1, 3)):
            art = random.choice([a for a in articulos if a["restaurante_id"] == rest["_id"]])
            cant = random.randint(1, 3)
            items.append({
                "articulo_id": art["_id"],
                "nombre": art["nombre"],
                "cantidad": cant,
                "precioUnitario": art["precio"]
            })
            total_price += cant * art["precio"]
        ordenes.append({
            "_id": ObjectId(),
            "usuario_id": user["_id"],
            "restaurante_id": rest["_id"],
            "fecha": (datetime.utcnow() - timedelta(days=random.randint(0, 90))).isoformat(),
            "estado": random.choice(["entregado", "en proceso", "cancelado"]),
            "total": round(total_price, 2),
            "items": items,
            "resenia_id": None
        })
    return ordenes

def generar_resenias(ordenes, max_res=3000):
    resenias = []
    for o in random.sample(ordenes, min(max_res, len(ordenes))):
        resenias.append({
            "_id": ObjectId(),
            "usuario_id": o["usuario_id"],
            "restaurante_id": o["restaurante_id"],
            "orden_id": o["_id"],
            "comentario": fake.sentence(),
            "calificacion": random.randint(1, 5),
            "fecha": o["fecha"]
        })
    return resenias

# Crear y guardar archivos
usuarios = generar_usuarios()
restaurantes = generar_restaurantes()
articulos = generar_articulos(restaurantes)
ordenes = generar_ordenes(usuarios, restaurantes, articulos)
resenias = generar_resenias(ordenes)


#with open("precarga_datos/usuarios.json", "w") as f: json.dump(usuarios, f)
#with open("precarga_datos/restaurantes.json", "w") as f: json.dump(restaurantes, f)
#with open("precarga_datos/articulos.json", "w") as f: json.dump(articulos, f)
#with open("precarga_datos/ordenes.json", "w") as f: json.dump(ordenes, f)
#with open("precarga_datos/resenias.json", "w") as f: json.dump(resenias, f)

# Al final del archivo, reemplaza la sección de guardar archivos con:
from pymongo import MongoClient

# Conectarse a MongoDB
client = MongoClient("mongodb+srv://<usuario>:<costraseña>@cluster0.dpdp0um.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")  
db = client["restaurante_db"]

# Insertar datos
db.usuarios.insert_many(usuarios)
db.restaurantes.insert_many(restaurantes)
db.articulos.insert_many(articulos)
db.ordenes.insert_many(ordenes)
db.resenias.insert_many(resenias)

print("Datos insertados directamente en MongoDB con ObjectId.")


print("Archivos .json generados.")
