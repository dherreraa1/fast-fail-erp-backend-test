FROM python:3.11-slim

# Crear directorio de trabajo
WORKDIR /code

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias de Python
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del proyecto
COPY . /code/
