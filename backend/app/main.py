"""
Point d'entrée principal de l'application SmartHome Lite.
Configure FastAPI, les middlewares, et enregistre toutes les routes.
"""
import asyncio
from contextlib import asynccontextmanager
import logging
import time

import httpx
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings, validate_production_config
from app.database import engine, Base, init_db, SessionLocal
from app.models import Device, RaspberryPi, LightReading
from app.services.device_service import DeviceService
from app.services.smart_dimming_service import SmartDimmingService

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
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Connexion base de données OK")
        try:
            init_db()
            logger.info("Schéma base de données initialisé")
        except Exception as e:
            logger.warning(f"Impossible d'initialiser le schéma BDD (peut-être déjà créé): {e}")
        
        # Créer l'admin par défaut s'il n'existe pas
        try:
            from app.database import SessionLocal
            from app.models import User
            from app.utils.auth import get_password_hash
            
            db = SessionLocal()
            try:
                admin_user = db.query(User).filter(User.username == "admin").first()
                if not admin_user:
                    hashed_password = get_password_hash("admin123")
                    admin_user = User(
                        username="admin",
                        email=None,
                        password_hash=hashed_password,
                        role="admin"
                    )
                    db.add(admin_user)
                    db.commit()
                    logger.info("Utilisateur admin créé automatiquement (username: admin, password: admin123)")
                else:
                    logger.debug("Utilisateur admin existe déjà")
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Impossible de créer l'admin par défaut: {e}")
    except Exception as e:
        logger.warning(
            f"Base de données non accessible: {e}\n"
            f"L'API démarrera mais les fonctionnalités nécessitant la BDD ne fonctionneront pas."
        )
        # Ne pas faire planter l'application si la BDD n'est pas disponible
        # L'utilisateur pourra toujours accéder à la documentation API
    
    # Chargement du modèle IA (si disponible)
    try:
        from app.services.ai_service import get_ai_service
        ai_service = get_ai_service()
        if ai_service.model is not None:
            logger.info("Modèle IA chargé avec succès")
        else:
            logger.warning("Aucun modèle IA trouvé, utilisation du mode fallback")
    except ImportError:
        logger.debug("Module ai_service non disponible (optionnel)")
    except Exception as e:
        logger.warning(f"Impossible de charger modèle IA: {e}")
    
    logger.info(f"API accessible sur http://{settings.api_host}:{settings.api_port}")

    # Heartbeat périodique : ping des RPi pour mettre à jour is_online
    _heartbeat_task = None

    async def _rpi_heartbeat_loop():
        """Ping périodique des RPi via GET / : si la RPi répond → is_online = True."""
        import os
        headers = {}
        key = getattr(settings, "raspberry_pi_api_key", None) or os.environ.get("RASPBERRY_API_KEY")
        if key:
            headers["X-API-Key"] = key.strip()
        interval = max(15, getattr(settings, "raspberry_pi_heartbeat_interval", 60))
        timeout = getattr(settings, "raspberry_pi_timeout", 5)
        await asyncio.sleep(3)  # Premier ping 3 s après démarrage
        while True:
            try:
                db = SessionLocal()
                try:
                    rpis = db.query(RaspberryPi).all()
                    for rpi in rpis:
                        url = f"{settings.raspberry_pi_protocol}://{rpi.ip_address}:{settings.raspberry_pi_port}/"
                        try:
                            async with httpx.AsyncClient(timeout=timeout) as client:
                                r = await client.get(url, headers=headers or None)
                                r.raise_for_status()
                            # RPi présente et répond → en ligne
                            if not rpi.is_online:
                                rpi.is_online = True
                                db.commit()
                                db.refresh(rpi)
                                logger.info(f"Raspberry Pi {rpi.name} is now online (GET / OK)")
                        except Exception as e:
                            # Ne pas passer is_online à False ici : le RPi peut être joignable
                            # via son heartbeat (GET /api/raspberry-pis/heartbeat) alors que le
                            # ping GET / depuis le backend échoue (réseau, firewall, IP incorrecte, etc.).
                            logger.info(
                                "Raspberry Pi %s ping échoué (URL: %s) — vérifier l'IP en base ou que le RPi appelle /api/raspberry-pis/heartbeat: %s",
                                rpi.name, url, e,
                            )
                finally:
                    db.close()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Heartbeat RPi error: {e}")
                await asyncio.sleep(interval)

    try:
        _heartbeat_task = asyncio.create_task(_rpi_heartbeat_loop())
        logger.info("Heartbeat RPi démarré (mise à jour is_online)")
    except Exception as e:
        logger.warning(f"Impossible de démarrer le heartbeat RPi: {e}")

    _sensor_control_task = None
    SENSOR_CONTROL_INTERVAL = 30

    async def _sensor_control_loop():
        """Périodiquement : récupère les données des capteurs qui pilotent au moins une lampe,
        applique les règles capteur→lampe et déclenche le smart dimming si luminosité dispo."""
        await asyncio.sleep(10)
        while True:
            try:
                db = SessionLocal()
                try:
                    # Uniquement les capteurs qui ont au moins une lampe liée (controlled_by_sensor_id)
                    sub = db.query(Device.controlled_by_sensor_id).filter(
                        Device.controlled_by_sensor_id.isnot(None),
                        Device.deleted_at.is_(None),
                    ).distinct()
                    sensors = db.query(Device).filter(
                        Device.type == "sensor",
                        Device.deleted_at.is_(None),
                        Device.id.in_(sub),
                    ).all()
                    for sensor in sensors:
                        try:
                            rpi = sensor.raspberry_pi
                            node_id = sensor.gpio_pin
                            svc = DeviceService(db)
                            data = await svc.get_sensor_data_from_rpi(rpi, node_id)
                            await svc.evaluate_sensor_rules(sensor.id, data)
                            # Si le capteur expose une luminosité (Z-Wave MultiSensor, etc.),
                            # l'utiliser aussi pour le Smart Dimming global.
                            lux = data.get("illuminance_lux")
                            if lux is not None:
                                reading = LightReading(
                                    raspberry_pi_id=rpi.id,
                                    lux_value=float(lux),
                                    # Typiquement BH1750 / LDR ; on réutilise ce champ
                                    # pour marquer une mesure issue d'un capteur Z-Wave.
                                    sensor_type="BH1750",
                                )
                                db.add(reading)
                                db.commit()
                                db.refresh(reading)

                                sd_service = SmartDimmingService(db)
                                await sd_service.process_light_reading(reading)
                        except Exception as e:
                            logger.debug("Sensor control %s (node %s): %s", sensor.name, sensor.gpio_pin, e)
                finally:
                    db.close()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("Sensor control loop error: %s", e)
            await asyncio.sleep(SENSOR_CONTROL_INTERVAL)

    try:
        _sensor_control_task = asyncio.create_task(_sensor_control_loop())
        logger.info("Pilotage lampes par capteur démarré (intervalle %s s)", SENSOR_CONTROL_INTERVAL)
    except Exception as e:
        logger.warning("Impossible de démarrer le pilotage capteur: %s", e)

    yield

    if _sensor_control_task and not _sensor_control_task.done():
        _sensor_control_task.cancel()
        try:
            await _sensor_control_task
        except asyncio.CancelledError:
            pass
        logger.info("Pilotage capteur arrêté")
    if _heartbeat_task and not _heartbeat_task.done():
        _heartbeat_task.cancel()
        try:
            await _heartbeat_task
        except asyncio.CancelledError:
            pass
        logger.info("Heartbeat RPi arrêté")

    logger.info("Arrêt SmartHome Lite API")
    engine.dispose()
    
    # Sauvegarde du modèle IA (si disponible)
    # Note: Le modèle est sauvegardé lors de l'entraînement, pas au shutdown
    logger.debug("Arrêt du service IA")


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

# Rate limiting (seulement en production ou si configuré)
if settings.is_production or not settings.debug:
    try:
        from app.middleware.rate_limit import RateLimitMiddleware
        app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
        logger.info("Rate limiting activé (60 requêtes/minute)")
    except Exception as e:
        logger.warning(f"Impossible d'activer le rate limiting: {e}")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log des requêtes HTTP avec temps de traitement et collecte de métriques."""
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log structuré
        logger.info(
            f"{request.method} {request.url.path} "
            f"[{response.status_code}] "
            f"({process_time:.3f}s) "
            f"- {client_ip}"
        )
        
        # Collecte de métriques
        try:
            from app.utils.metrics import get_metrics_collector
            metrics = get_metrics_collector()
            metrics.record_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                process_time=process_time
            )
        except Exception:
            pass  # Ne pas faire planter la requête si les métriques échouent
        
        response.headers["X-Process-Time"] = str(process_time)
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"{request.method} {request.url.path} "
            f"[ERROR] ({process_time:.3f}s) - {client_ip}: {str(e)}",
            exc_info=True
        )
        
        # Enregistrer l'erreur dans les métriques
        try:
            from app.utils.metrics import get_metrics_collector
            metrics = get_metrics_collector()
            metrics.record_request(
                endpoint=request.url.path,
                method=request.method,
                status_code=500,
                process_time=process_time
            )
        except Exception:
            pass
        
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
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Vérification de santé de l'API."""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception as e:
        database_status = f"error: {str(e)}"
    
    # Vérifier le service IA
    ai_status = "unknown"
    try:
        from app.services.ai_service import get_ai_service
        ai_service = get_ai_service()
        ai_status = "loaded" if ai_service.model is not None else "fallback"
    except Exception:
        ai_status = "error"
    
    # Vérifier le service de régression
    regression_status = "unknown"
    try:
        from app.services.regression_service import get_regression_service
        regression_service = get_regression_service()
        regression_status = "loaded" if regression_service.model is not None else "fallback"
    except Exception:
        regression_status = "error"
    
    # Vérifier Ollama
    ollama_status = "disabled"
    try:
        from app.services.ollama_service import OllamaService
        ollama_service = OllamaService()
        ollama_status = "enabled" if ollama_service.enabled else "disabled"
    except Exception:
        ollama_status = "error"
    
    return {
        "status": "healthy",
        "database": database_status,
        "ai_service": ai_status,
        "regression_service": regression_status,
        "ollama": ollama_status,
        "environment": settings.environment
    }


# Enregistrement des routes
from app.routes import auth, devices, events, rules, ai, smart_dimming, raspberry_pis, light_readings, presence, admin

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(devices.router, prefix="/api/devices", tags=["Devices"])
app.include_router(events.router, prefix="/api/events", tags=["Events"])
app.include_router(rules.router, prefix="/api/rules", tags=["Rules"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(smart_dimming.router, prefix="/api/smart-dimming", tags=["Smart Dimming"])
app.include_router(raspberry_pis.router, prefix="/api/raspberry-pis", tags=["Raspberry Pi"])
app.include_router(light_readings.router, prefix="/api/light-readings", tags=["Light Readings"])
app.include_router(presence.router, prefix="/api/presence", tags=["Presence"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])