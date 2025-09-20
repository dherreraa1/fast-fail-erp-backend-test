# Gestión de Documentos - ERP

Módulo de gestión de documentos para ERP que permite almacenar archivos en la nube (AWS S3), referenciarlos en base de datos PostgreSQL y validarlos mediante un flujo jerárquico de aprobaciones.

## Características

- **Almacenamiento en la nube**: Integración con AWS S3 usando pre-signed URLs
- **Metadatos estructurados**: PostgreSQL para información de documentos y validaciones
- **Flujo de validación jerárquico**: Sistema de aprobaciones con reglas de jerarquía
- **APIs REST**: Endpoints para carga, descarga, aprobación y rechazo
- **Trazabilidad completa**: Auditoría de todas las acciones realizadas
- **Autenticación JWT**: Seguridad integrada con tokens

## Tecnologías

- **Backend**: Django 5.0.6 + Django REST Framework
- **Base de datos**: PostgreSQL 15
- **Storage**: AWS S3 (con soporte para LocalStack/MinIO)
- **Autenticación**: JWT (Simple JWT)
- **Testing**: pytest + pytest-django
- **Containerización**: Docker + Docker Compose

## Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# Configuración base de datos
POSTGRES_DB=erp_db
POSTGRES_USER=erp_user
POSTGRES_PASSWORD=erp_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Configuración Django
DJANGO_SECRET_KEY=django-insecure-secret-key-change-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*

# Configuración AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_REGION=us-east-1
AWS_S3_ENDPOINT=  # Opcional
AWS_PRESIGNED_EXPIRATION=3600
```

## Instalación y Configuración

### Docker

```bash
# 1. Clonar el repositorio
git clone https://github.com/dherreraa1/fast-fail-erp-backend-test 
cd fast-fail-erp-backend-test

# 3. Levantar servicios
docker-compose up -d

# 4. Ejecutar migraciones
docker-compose exec web python manage.py makemigrations users
docker-compose exec web python manage.py makemigrations app
docker-compose exec web python manage.py migrate
```

## Ejecutar Pruebas

```bash
# Con Docker
docker-compose exec web pytest tests/ -v

# Prueba específica
docker-compose exec web pytest tests/test_documents.py::test_upload_document_creates_metadata -v
```

## Estructura del Proyecto

```
fast-fail-test/
├── erp_backend/          # Configuración Django
│   ├── settings.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── urls.py
├── app/                  # Módulo principal de documentos
│   ├── models.py        # Company, Document, ValidationStep, ValidationAction
│   ├── views.py         # DocumentViewSet con endpoints
│   ├── serializers.py   # Serializers para APIs
│   ├── storage.py       # Integración con S3
│   └── urls.py          # URLs del módulo
├── users/               # Módulo de usuarios
│   ├── apps.py
│   ├── models.py        
│   ├── views.py         
│   ├── serializers.py          
│   └── urls.py          
├── tests/               # Pruebas automatizadas
│   ├── conftest.py
│   ├── test_auth.py        
│   ├── test_documents.py                   
│   └── test_validation.py
└── manage.py
└── requirements.txt
└── README.md
└── Dockerfile
└── docker-compose.yml
```

## Uso de la API

### Configuración inicial

Antes de usar la API, necesitas crear usuarios y empresas:

```bash
# 1. Crear usuario
curl -X POST http://localhost:8000/api/auth/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass", "email": "test@example.com"}'

# 2. Obtener token JWT
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'

# Respuesta:
# {
#   "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
#   "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
# }

# 3. Crear una empresa (usar el token obtenido)
curl -X POST http://localhost:8000/api/companies/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Company"}'

# Respuesta incluirá el company_id requerido para crear documentos
```

**Nota**: Para facilitar el registro de usuarios, el endpoint `/api/auth/users/` permite creación sin autenticación. En producción esto se restringiría adecuadamente.

### Flujo completo de ejemplo

Una vez se haya obtenido el token y el company_id de los pasos anteriores, se utilizan los IDs reales:

```bash
# Ejemplo usando IDs reales 
# Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
# Company ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
# User ID: u1v2w3x4-y5z6-7890-abcd-ef1234567890
```

### 1. Cargar Documento

```bash
curl -X POST http://localhost:8000/api/documents/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "entity": {
      "entity_type": "vehicle",
      "entity_id": "00000000-0000-0000-0000-000000000000"
    },
    "document": {
      "name": "soat.pdf",
      "mime_type": "application/pdf",
      "size_bytes": 123456,
      "bucket_key": "companies/a1b2c3d4-e5f6-7890-abcd-ef1234567890/vehicles/docs/soat-2025.pdf"
    },
    "validation_flow": {
      "enabled": true,
      "steps": [
        {"order": 1, "approver_user_id": "u1v2w3x4-y5z6-7890-abcd-ef1234567890"},
        {"order": 2, "approver_user_id": "u1v2w3x4-y5z6-7890-abcd-ef1234567890"}
      ]
    }
  }'
```

**Respuesta:**
```json
{
  "document_id": "d1e2f3g4-h5i6-7890-abcd-ef1234567890",
  "upload_url": "https://test-bucket.s3.amazonaws.com/presigned-put-url..."
}
```

### 2. Descargar Documento

```bash
curl -X GET http://localhost:8000/api/documents/d1e2f3g4-h5i6-7890-abcd-ef1234567890/download/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

**Respuesta:**
```json
{
  "download_url": "https://test-bucket.s3.amazonaws.com/presigned-get-url...",
  "validation_status": "P"
}
```

### 3. Aprobar Documento

```bash
curl -X POST http://localhost:8000/api/documents/d1e2f3g4-h5i6-7890-abcd-ef1234567890/approve/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "actor_user_id": "u1v2w3x4-y5z6-7890-abcd-ef1234567890",
    "reason": "Documento cumple con todos los requisitos"
  }'
```

**Respuesta:**
```json
{
  "detail": "Aprobado",
  "document_status": "A"
}
```

### 4. Rechazar Documento

```bash
curl -X POST http://localhost:8000/api/documents/d1e2f3g4-h5i6-7890-abcd-ef1234567890/reject/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "actor_user_id": "u1v2w3x4-y5z6-7890-abcd-ef1234567890",
    "reason": "Documento ilegible, favor reenviar"
  }'
```

**Respuesta:**
```json
{
  "detail": "Rechazado",
  "document_status": "R"
}
```

### Obtener información de documentos

```bash
# Listar todos los documentos
curl -X GET http://localhost:8000/api/documents/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

# Ver detalles de un documento específico
curl -X GET http://localhost:8000/api/documents/d1e2f3g4-h5i6-7890-abcd-ef1234567890/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## Modelos de Datos

### Document
- `company`: Referencia a la empresa
- `entity_type/entity_id`: Referencia genérica a entidades (vehicle, employee, etc.)
- `validation_status`: null (sin validación), P (pendiente), A (aprobado), R (rechazado)

### ValidationStep
- `order`: Orden jerárquico (mayor = más jerarquía)
- `approver`: Usuario aprobador
- `approved/rejected`: Estado del paso

### ValidationAction
- Registro de trazabilidad de todas las acciones de aprobación/rechazo

## Reglas de Negocio

1. **Jerarquía**: `order` más alto = mayor jerarquía
2. **Auto-aprobación**: Aprobador de mayor jerarquía aprueba automáticamente los pasos previos
3. **Estado terminal**: Un rechazo pone el documento en estado R (terminal)
4. **Trazabilidad**: Todas las acciones se registran en ValidationAction

## Estados de Validación

- **null**: Documento sin flujo de validación
- **P**: Pendiente de aprobación
- **A**: Aprobado (todos los pasos completados)
- **R**: Rechazado (estado terminal)

## Desarrollo

```bash
# Ejecutar en modo desarrollo
docker-compose up

# Ver logs
docker-compose logs -f web

# Entrar al contenedor
docker-compose exec web bash

# Ejecutar comandos Django
docker-compose exec web python manage.py shell
```

## Configuración de Producción

1. **Cambiar `DJANGO_SECRET_KEY`** por una clave segura
2. **Configurar `DJANGO_DEBUG=False`**
3. **Configurar credenciales reales de AWS S3**
4. **Usar base de datos PostgreSQL externa**
5. **Configurar CORS y CSRF según necesidades**
6. **Implementar SSL/TLS**

## Troubleshooting

### Error de migraciones
```bash
# Reset completo de BD (solo desarrollo)
docker-compose down -v
docker-compose up -d
docker-compose exec web python manage.py migrate
```

### Error de AWS S3
- Verificar credenciales en `.env`
- Para desarrollo local usar LocalStack o MinIO
- Las pruebas usan mocks automáticos

### Error de permisos
- Verificar que el usuario esté autenticado
- Verificar que el token JWT sea válido
- Verificar permisos del usuario sobre la empresa/entidad