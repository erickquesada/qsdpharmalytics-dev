# 🚨 ATUALIZAÇÃO URGENTE - Node 20

## ⚠️ Novo Problema Identificado

O deploy falhou com o erro:
```
error react-router-dom@7.9.4: The engine "node" is incompatible with this module. 
Expected version ">=20.0.0". Got "18.20.8"
```

## ✅ Solução Aplicada

**Dockerfile.frontend.production atualizado:**
- ❌ Antes: `FROM node:18-alpine`
- ✅ Agora: `FROM node:20-alpine`

## 🚀 Como Atualizar

No seu servidor:

```bash
cd /opt/qsdpharma
git pull origin main
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up --build -d
```

## 📊 O que foi corrigido?

### Correção 1: Backend (já estava corrigido)
- ✅ BACKEND_CORS_ORIGINS parser
- ✅ Imports do entrypoint
- ✅ Alembic database URL

### Correção 2: Frontend (NOVA)
- ✅ Node atualizado de 18 para 20
- ✅ Compatível com react-router-dom 7.9.4

## 🎯 Teste Rápido

Após o rebuild:

```bash
# Verificar containers
docker ps

# Ver logs backend
docker logs qsdpharma_backend --tail 20

# Ver logs frontend
docker logs qsdpharma_frontend --tail 20

# Testar API
curl http://localhost:8001/api/v1/health
```

## 📝 Arquivo .env (lembrete)

Certifique-se que seu `.env` tem:

```bash
POSTGRES_PASSWORD=SuaSenhaForte123
SECRET_KEY=sua_chave_de_32_caracteres
BACKEND_CORS_ORIGINS=["https://qsdpharma.qsdconnect.cloud"]
```

## ✨ Status Atual

- ✅ Backend corrigido
- ✅ Frontend corrigido
- ✅ Node 20 configurado
- ✅ Docker Compose atualizado
- ✅ Pronto para deploy

## 🆘 Se ainda falhar

Limpe tudo e rebuilde:

```bash
cd /opt/qsdpharma
docker-compose -f docker-compose.production.yml down -v
docker system prune -f
docker-compose -f docker-compose.production.yml up --build -d
```

Depois verifique os logs:
```bash
docker logs qsdpharma_backend -f
```
