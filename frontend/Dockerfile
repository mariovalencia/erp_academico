FROM node:22-alpine

WORKDIR /app

# Instalar Angular CLI globalmente
RUN npm install -g @angular/cli@20

# Copiar package.json e instalar dependencias
COPY package*.json ./
RUN npm install

# Copiar código de la aplicación
COPY . .

# Copiar archivo de entorno específico del frontend
COPY .env.frontend .env

# Exponer puerto
EXPOSE 4200

# Comando de desarrollo
CMD ["ng", "serve", "--host", "0.0.0.0", "--port", "4200", "--poll", "2000"]