from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient
from bson import ObjectId
import os

app = FastAPI()

# Conexão com MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = MongoClient(MONGO_URL)
db = client["alunia"]
empresas_collection = db["empresas"]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos
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
    tempo_resposta: Optional[str] = "2 horas"
    tempo_ativado: Optional[bool] = True
    opcoes_mensagem: Optional[List[str]] = []
    links_externos: Optional[List[str]] = []

# Teste
@app.get("/")
def root():
    return {"status": "API AluniA com MongoDB no ar!"}

# Login
@app.post("/login")
def login_empresa(login: dict = Body(...)):
    email = login.get("email")
    senha = login.get("senha")

    empresa = empresas_collection.find_one({"email": email, "senha": senha})
    if not empresa:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    return {
        "message": "Login OK",
        "empresa": {
            "id": str(empresa["_id"]),
            "nome": empresa["nome"],
            "email": empresa["email"],
            "numero": empresa["numero"],
            "plano": empresa["plano"],
            "senha": empresa["senha"]
        }
    }

# Listar todas empresas
@app.get("/empresas")
def listar_empresas():
    empresas = list(empresas_collection.find({}))
    for e in empresas:
        e["id"] = str(e["_id"])
        del e["_id"]
    return empresas

# Buscar uma empresa específica
@app.get("/empresas/{email}")
def buscar_empresa(email: str):
    empresa = empresas_collection.find_one({"email": email})
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    empresa["id"] = str(empresa["_id"])
    del empresa["_id"]
    return empresa

# Cadastrar nova empresa
@app.post("/empresas")
def criar_empresa(dados: Empresa):
    if empresas_collection.find_one({"email": dados.email}):
        raise HTTPException(status_code=400, detail="Empresa já cadastrada")
    nova = empresas_collection.insert_one(dados.dict())
    return {"id": str(nova.inserted_id)}

# Atualizar dados da empresa
@app.put("/empresas/{email}")
def atualizar_empresa(email: str, dados: dict = Body(...)):
    empresa = empresas_collection.find_one({"email": email})
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    empresas_collection.update_one({"email": email}, {"$set": dados})
    return {"message": "Empresa atualizada com sucesso"}

# Resetar senha
@app.patch("/empresas/{empresa_id}/reset")
def resetar_senha(empresa_id: str):
    result = empresas_collection.update_one(
        {"_id": ObjectId(empresa_id)},
        {"$set": {"senha": "alunia@123"}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")
    return {"message": "Senha resetada para 'alunia@123'"}
