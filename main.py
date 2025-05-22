
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient
from bson import ObjectId
import os

app = FastAPI()

# Conexão com o MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = MongoClient(MONGO_URL)
db = client["alunia"]
empresas_collection = db["empresas"]

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Horario(BaseModel):
    dia: str
    inicio: str
    fim: str
    ativo: bool

class Empresa(BaseModel):
    nome: str
    email: str
    senha: str
    numero: str
    plano: str
    mensagem_inicial: Optional[str] = ""
    mensagem_fora_horario: Optional[str] = ""
    horario_funcionamento: Optional[List[Horario]] = []

# Utils
class PyObjectId(ObjectId):
    @classmethod
    def get_validators(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

# Rotas principais
@app.get("/empresas")
def listar_empresas():
    empresas = list(empresas_collection.find({}, {"senha": 0}))
    for e in empresas:
        e["_id"] = str(e["_id"])
    return empresas

@app.post("/empresas")
def criar_empresa(dados: Empresa):
    if empresas_collection.find_one({"email": dados.email}):
        raise HTTPException(status_code=400, detail="Empresa já cadastrada")
    nova = empresas_collection.insert_one(dados.dict())
    return {"id": str(nova.inserted_id)}

@app.get("/empresas/{email}")
def buscar_empresa(email: str):
    empresa = empresas_collection.find_one({"email": email})
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    empresa["_id"] = str(empresa["_id"])
    return empresa

@app.put("/empresas/{email}")
def atualizar_empresa(email: str, dados: Empresa):
    resultado = empresas_collection.update_one({"email": email}, {"$set": dados.dict()})
    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return {"msg": "Atualizado com sucesso"}

@app.delete("/empresas/{email}")
def remover_empresa(email: str):
    resultado = empresas_collection.delete_one({"email": email})
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return {"msg": "Empresa removida"}
