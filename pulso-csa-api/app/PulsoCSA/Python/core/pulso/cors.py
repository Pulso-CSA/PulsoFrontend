# api/app/core/app/cors.py
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

def setup_cors(app, origins: Optional[List[str]] = None) -> None:
    if origins is None:
        # ORIGENS DE DESENVOLVIMENTO COMUNS (ajuste se usar outra porta/host)
        origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],   # inclui OPTIONS (preflight)
        allow_headers=["*"],   # inclui Content-Type: application/json
    )
