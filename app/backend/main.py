"""API del dashboard de Modelo Fly (FastAPI). Sirve también el frontend de `app/frontend/`.

Arranque, desde la raíz del repositorio:
    uvicorn app.backend.main:app --port 8000
y abrir http://localhost:8000. La primera vez tarda ~2 min (lee el Excel y entrena el Random Forest);
las siguientes, ~40 s (el Random Forest queda guardado en models/).
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from .servicio import Servicio  # noqa: E402  (necesita src/ en el path)

FRONTEND = ROOT / "app" / "frontend"
servicio = Servicio()


@asynccontextmanager
async def ciclo(app):
    servicio.iniciar()
    yield


app = FastAPI(title="Modelo Fly · Dashboard", lifespan=ciclo)


def _listo():
    if servicio.estado != "listo":
        raise HTTPException(503, "El modelo todavía se está cargando" if servicio.estado == "cargando" else servicio.error)


class Opinion(BaseModel):
    outfit_id: str
    aceptado: bool


@app.get("/api/estado")
def estado():
    return servicio.info()


@app.get("/api/usuarios")
def usuarios():
    _listo()
    return servicio.usuarios()


@app.get("/api/usuarios/{user_id}")
def usuario(user_id: str):
    _listo()
    try:
        return servicio.usuario(user_id)
    except KeyError:
        raise HTTPException(404, f"No existe el usuario {user_id}")


@app.post("/api/usuarios/{user_id}/recomendar")
def recomendar(user_id: str):
    _listo()
    try:
        return servicio.recomendar(user_id)
    except KeyError:
        raise HTTPException(404, f"No existe el usuario {user_id}")


@app.post("/api/opiniones")
def opinar(op: Opinion):
    _listo()
    try:
        servicio.opinar(op.outfit_id, op.aceptado)
    except KeyError:
        raise HTTPException(404, f"No existe la recomendación {op.outfit_id}")
    return {"ok": True}


@app.get("/api/resumen")
def resumen():
    _listo()
    return servicio.resumen()


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/")
def inicio():
    return FileResponse(FRONTEND / "index.html")
