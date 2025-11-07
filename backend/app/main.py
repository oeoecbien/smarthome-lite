"""
Point d'entrée principal de l'application SmartHome Lite.
Configure FastAPI, les middlewares, et enregistre toutes les routes.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time

from app.config import settings, validate_production_config
from app.database import engine, Base, init_db

logging.basicConfig(
    level=settings.log_level,
    format=settings.log_format,
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application.
    Startup: validation config, connexion BDD, chargement modèle IA
    Shutdown: fermeture connexions, sauvegarde modèle
    """
    logger.info("Démarrage SmartHome Lite API")
    
    try:
        validate_production_config()
    except RuntimeError as e:
        logger.error(f"Erreur configuration: {e}")
        raise
    
    logger.info(f"Connexion à PostgreSQL {settings.database_host}:{settings.database_port}")
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Connexion base de données OK")
        init_db()
        logger.info("Schéma base de données initialisé")
    except Exception as e:
        logger.error(f"Erreur connexion BDD: {e}")
        raise
    
    try:
        from app.services.ml_service import load_model
        if load_model():
            logger.info("Modèle IA chargé")
        else:
            logger.warning("Aucun modèle IA trouvé")
    except Exception as e:
        logger.warning(f"Impossible de charger modèle IA: {e}")
    
    logger.info(f"API accessible sur http://{settings.api_host}:{settings.api_port}")
    
    yield
    
    logger.info("Arrêt SmartHome Lite API")
    engine.dispose()
    
    try:
        from app.services.ml_service import save_model_if_trained
        save_model_if_trained()
    except Exception as e:
        logger.warning(f"Impossible de sauvegarder modèle IA: {e}")


app = FastAPI(
    title="SmartHome Lite API",
    description="API REST pour système domotique intelligent",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    debug=settings.debug,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if not settings.debug else ["*"],
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log des requêtes HTTP avec temps de traitement."""
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            f"{request.method} {request.url.path} "
            f"[{response.status_code}] "
            f"({process_time:.3f}s) "
            f"- {client_ip}"
        )
        
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"{request.method} {request.url.path} "
            f"[ERROR] ({process_time:.3f}s) - {client_ip}: {str(e)}"
        )
        raise


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Gestion des erreurs de validation Pydantic."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Erreur validation sur {request.url.path}: {errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Erreur de validation des données",
            "errors": errors
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Gestion des erreurs non capturées."""
    logger.error(f"Erreur non gérée sur {request.url.path}: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Erreur interne du serveur",
            "error": str(exc) if settings.debug else "Une erreur est survenue"
        }
    )


@app.get("/", tags=["Root"])
def root():
    """Point d'entrée racine de l'API."""
    return {
        "message": "SmartHome Lite API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Vérification de santé de l'API."""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        database_status = "connected"
    except Exception as e:
        database_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": database_status,
        "environment": settings.environment
    }


# Enregistrement des routes
# from app.routes import auth, devices, events, rules, ai, smart_dimming, raspberry_pis
# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
# app.include_router(events.router, prefix="/api/events", tags=["Events"])
# app.include_router(rules.router, prefix="/api/rules", tags=["Rules"])
# app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
# app.include_router(smart_dimming.router, prefix="/api/smart-dimming", tags=["Smart Dimming"])
# app.include_router(raspberry_pis.router, prefix="/api/raspberry-pis", tags=["Raspberry Pi"])
