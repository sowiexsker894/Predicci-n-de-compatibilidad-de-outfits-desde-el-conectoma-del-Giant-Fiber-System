"""Estado del dashboard: la BD común en memoria, los modelos y un escritor del Excel en segundo plano.

Abrir y guardar `BD_modelo_fly.xlsx` con openpyxl tarda 2–3 min (15 MB), así que la API responde al
momento y las escrituras (recomendaciones nuevas y opiniones me gusta / no me gusta) se encolan. El
escritor junta todo lo pendiente en una sola apertura del libro.
"""

import os
import queue
import threading
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from openpyxl import load_workbook

from modelo_fly.caracteristicas import GRUPOS_SLOT
from modelo_fly.deepfm_numpy import DeepFMNumpy
from modelo_fly.recomendador import ALFA, BETA, EXPERIMENTO, cargar_modelos, guardar, leer_bd, recomendar

ROOT = Path(__file__).resolve().parents[2]
RUTA_BD = Path(os.environ.get("MODELO_FLY_BD", ROOT / "data" / "BD_modelo_fly.xlsx"))
RUTA_RF = ROOT / "models" / "fase2_random_forest.joblib"  # caché local (models/ está en .gitignore)
PERFIL = ["user_id", "grupo", "estilo_fav", "edad", "genero", "ciudad", "clima", "n_closet"]
ATRIB_PRENDA = ["item_id", "origen", "name", "slot", "tono", "familia_color", "patron", "material", "estilo", "epoca"]
ORDEN_SLOT = ["exterior", "arriba", "vestido", "abajo", "calzado", "bolso", "accesorio", "joyeria"]


class Servicio:
    def __init__(self, ruta_bd=RUTA_BD):
        self.ruta_bd = Path(ruta_bd)
        self.estado, self.error = "cargando", None
        self.lock = threading.Lock()
        self.cola = queue.Queue()
        self.pendientes, self.ultima_escritura, self.error_escritura = 0, None, None

    # ---------- carga ----------
    def iniciar(self):
        threading.Thread(target=self._cargar, daemon=True).start()
        threading.Thread(target=self._escritor, daemon=True).start()

    def _cargar(self):
        try:
            t = time.time()
            self.bd = leer_bd(self.ruta_bd)
            libro = pd.ExcelFile(self.ruta_bd)
            self.pred = pd.read_excel(libro, sheet_name="predicciones", dtype={"user_id": str})
            self.metricas = pd.read_excel(libro, sheet_name="metricas")
            self.impacto = pd.read_excel(libro, sheet_name="impacto_ods")
            self.items = self.bd["items"].set_index("item_id")[ATRIB_PRENDA[1:]]
            self.deepfm, self.rf_ttmn, self.rf_dlmn = self._modelos()
            self.estado = "listo"
            print(f"[dashboard] listo en {time.time() - t:.0f} s")
        except Exception as e:  # se muestra en /api/estado
            self.estado, self.error = "error", f"{type(e).__name__}: {e}"
            raise

    def _modelos(self):
        if RUTA_RF.exists():
            deepfm = DeepFMNumpy(ROOT / "models" / "deepfm_pesos.npz", list(GRUPOS_SLOT.values()))
            rf_ttmn, rf_dlmn = joblib.load(RUTA_RF)
            return deepfm, rf_ttmn, rf_dlmn
        deepfm, rf_ttmn, rf_dlmn = cargar_modelos(ROOT)  # ~1,5 min la primera vez
        joblib.dump((rf_ttmn, rf_dlmn), RUTA_RF, compress=3)
        return deepfm, rf_ttmn, rf_dlmn

    # ---------- lectura ----------
    def info(self):
        return {"estado": self.estado, "error": self.error, "escrituras_pendientes": self.pendientes,
                "ultima_escritura": self.ultima_escritura, "error_escritura": self.error_escritura,
                "bd": self.ruta_bd.name, "experimento": EXPERIMENTO, "alfa": ALFA, "beta": BETA}

    def usuarios(self):
        u = self.bd["usuarios"][PERFIL]
        return u.to_dict("records")

    def _prendas(self, ids):
        filas = self.items.reindex(ids).reset_index().rename(columns={"index": "item_id"})
        filas = filas.fillna("desconocido")
        filas["orden"] = filas["slot"].map({s: i for i, s in enumerate(ORDEN_SLOT)}).fillna(99)
        return filas.sort_values("orden").drop(columns="orden").to_dict("records")

    def usuario(self, user_id):
        u = self.bd["usuarios"]
        fila = u[u["user_id"] == user_id]
        if fila.empty:
            raise KeyError(user_id)
        closet = self.bd["closets"].loc[self.bd["closets"]["user_id"] == user_id, "item_id"].tolist()
        hist = self.bd["historial"][self.bd["historial"]["user_id"] == user_id]
        with self.lock:
            previas = self.pred[(self.pred["user_id"] == user_id) & (self.pred["origen"] == "recomendar")]
            previas = previas.sort_values(["fecha", "rango"], ascending=[False, True]).head(9)
        return {
            "perfil": fila[PERFIL].iloc[0].to_dict(),
            "closet": self._prendas(closet),
            "historial": {"outfits_vistos": int(len(hist)), "aceptados": int(hist["aceptado"].astype(int).sum())},
            "recomendaciones_previas": [self._outfit(r) for r in previas.to_dict("records")],
        }

    def _outfit(self, r):
        acept = r.get("aceptado")
        acept = None if acept is None or acept == "" or (isinstance(acept, float) and np.isnan(acept)) else int(acept)
        return {"outfit_id": r["outfit_id"], "rango": int(r["rango"]), "fecha": str(r["fecha"]),
                "p_deepfm": float(r["p_deepfm"]), "p_ttmn": float(r["p_ttmn"]), "dlmn": float(r["dlmn"]),
                "score_final": float(r["score_final"]), "aceptado": acept,
                "prendas": self._prendas(str(r["item_ids"]).split("|"))}

    def resumen(self):
        m = self.metricas
        rk = m[m["fuente"].str.startswith("07d") & (m["metrica"] == "NDCG@5")]
        rk = rk.groupby(["experimento", "modelo"], sort=False)["valor"].mean().reset_index()
        return {"ranking": rk.round(4).to_dict("records"),
                "impacto": self.impacto.fillna("").astype(str).to_dict("records")}

    # ---------- escritura ----------
    def recomendar(self, user_id):
        with self.lock:
            cand, rec = recomendar(user_id, self.ruta_bd, self.deepfm, self.rf_ttmn, self.rf_dlmn,
                                   escribir=False, bd=self.bd)
            rec = rec.assign(aceptado=np.nan)
            self.pred = pd.concat([self.pred, rec], ignore_index=True)
        self._encolar(("filas", cand, rec))
        return [self._outfit(r) for r in rec.to_dict("records")]

    def opinar(self, outfit_id, aceptado):
        with self.lock:
            fila = self.pred["outfit_id"] == outfit_id
            if not fila.any():
                raise KeyError(outfit_id)
            self.pred.loc[fila, "aceptado"] = int(aceptado)
        self._encolar(("opinion", outfit_id, int(aceptado)))

    def _encolar(self, op):
        self.pendientes += 1
        self.cola.put(op)

    def _escritor(self):
        while True:
            ops = [self.cola.get()]
            while not self.cola.empty():
                ops.append(self.cola.get_nowait())
            try:
                filas = [o for o in ops if o[0] == "filas"]
                if filas:  # guardar() abre y cierra el libro una vez para todas las filas nuevas
                    guardar(self.ruta_bd, pd.concat([o[1] for o in filas]), pd.concat([o[2] for o in filas]))
                opiniones = {o[1]: o[2] for o in ops if o[0] == "opinion"}  # la última opinión gana
                if opiniones:
                    self._guardar_opiniones(opiniones)
                self.ultima_escritura, self.error_escritura = time.strftime("%H:%M:%S"), None
            except Exception as e:
                self.error_escritura = f"{type(e).__name__}: {e}"
            finally:
                self.pendientes -= len(ops)

    def _guardar_opiniones(self, opiniones):
        libro = load_workbook(self.ruta_bd)
        ws = libro["predicciones"]
        col = {c.value: i for i, c in enumerate(ws[1])}
        for fila in ws.iter_rows(min_row=2):
            v = opiniones.get(fila[col["outfit_id"]].value)
            if v is not None:
                fila[col["aceptado"]].value = v
        libro.save(self.ruta_bd)
