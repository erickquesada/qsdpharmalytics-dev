from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, Any
import psutil
import os

from app.database import database_health_check
from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Endpoint completo de health check"""
    
    # Informações básicas da aplicação
    app_info = {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEBUG else "production",
        "timestamp": datetime.now().isoformat(),
    }
    
    # Health check do banco de dados
    database_info = database_health_check()
    
    # Informações do sistema
    system_info = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_usage": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent,
            "used": psutil.virtual_memory().used
        },
        "disk_usage": {
            "total": psutil.disk_usage('.').total,
            "used": psutil.disk_usage('.').used,
            "free": psutil.disk_usage('.').free,
            "percent": (psutil.disk_usage('.').used / psutil.disk_usage('.').total) * 100
        },
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
    }
    
    # Status geral
    overall_status = "healthy"
    issues = []
    
    # Verificar problemas
    if database_info["connection_status"] != "healthy":
        overall_status = "degraded"
        issues.append("Database connection issues")
    
    if system_info["memory_usage"]["percent"] > 90:
        overall_status = "degraded"
        issues.append("High memory usage")
    
    if system_info["disk_usage"]["percent"] > 90:
        overall_status = "degraded"
        issues.append("High disk usage")
    
    response = {
        "status": overall_status,
        "issues": issues,
        "application": app_info,
        "database": database_info,
        "system": system_info,
        "checks": {
            "database": database_info["connection_status"] == "healthy",
            "memory": system_info["memory_usage"]["percent"] < 90,
            "disk": system_info["disk_usage"]["percent"] < 90,
        }
    }
    
    # Se há problemas críticos, retornar erro HTTP
    if overall_status == "unhealthy":
        raise HTTPException(status_code=503, detail=response)
    
    return response

@router.get("/health/database")
async def database_health() -> Dict[str, Any]:
    """Health check específico do banco de dados"""
    
    db_info = database_health_check()
    
    if db_info["connection_status"] != "healthy":
        raise HTTPException(status_code=503, detail=db_info)
    
    return db_info

@router.get("/health/system")  
async def system_health() -> Dict[str, Any]:
    """Health check específico do sistema"""
    
    try:
        system_info = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": psutil.boot_time(),
            "cpu": {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            },
            "memory": {
                "virtual": psutil.virtual_memory()._asdict(),
                "swap": psutil.swap_memory()._asdict(),
            },
            "disk": {
                "usage": psutil.disk_usage('.')._asdict(),
                "io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None,
            },
            "network": {
                "io": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None,
                "connections": len(psutil.net_connections()),
            },
            "processes": {
                "count": len(psutil.pids()),
                "current_process": {
                    "pid": os.getpid(),
                    "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                    "cpu_percent": psutil.Process().cpu_percent(),
                }
            }
        }
        
        return {
            "status": "healthy",
            "system": system_info
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "error": str(e)
        })

@router.get("/health/detailed")
async def detailed_health() -> Dict[str, Any]:
    """Health check detalhado combinando todos os aspectos"""
    
    try:
        # Combinar todos os health checks
        basic_health = await health_check()
        system_details = await system_health()
        
        return {
            **basic_health,
            "detailed_system": system_details["system"],
            "recommendations": generate_recommendations(basic_health)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "error": str(e)
        })

def generate_recommendations(health_data: Dict[str, Any]) -> list:
    """Gerar recomendações baseadas no health check"""
    
    recommendations = []
    
    # Recomendações de memória
    memory_percent = health_data["system"]["memory_usage"]["percent"]
    if memory_percent > 80:
        recommendations.append({
            "type": "memory",
            "severity": "high" if memory_percent > 90 else "medium",
            "message": f"High memory usage ({memory_percent:.1f}%). Consider scaling up or optimizing queries.",
            "action": "Monitor memory usage and consider increasing system resources"
        })
    
    # Recomendações de disco
    disk_percent = health_data["system"]["disk_usage"]["percent"]
    if disk_percent > 80:
        recommendations.append({
            "type": "disk",
            "severity": "high" if disk_percent > 90 else "medium", 
            "message": f"High disk usage ({disk_percent:.1f}%). Clean up old backups or logs.",
            "action": "Run cleanup scripts or increase disk space"
        })
    
    # Recomendações de banco
    if health_data["database"]["connection_status"] != "healthy":
        recommendations.append({
            "type": "database",
            "severity": "critical",
            "message": "Database connection issues detected.",
            "action": "Check database server status and connection parameters"
        })
    
    db_response_time = health_data["database"].get("response_time_ms", 0)
    if db_response_time > 1000:
        recommendations.append({
            "type": "database",
            "severity": "medium",
            "message": f"Slow database response time ({db_response_time}ms).",
            "action": "Optimize queries or check database performance"
        })
    
    return recommendations