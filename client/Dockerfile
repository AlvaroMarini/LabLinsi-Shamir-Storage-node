# Etapa 1: Compilación de React
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Pasamos la API KEY en tiempo de compilación (reemplazá con la tuya del .env)
ARG VITE_API_KEY=tu_clave_secreta_aqui
ENV VITE_API_KEY=$VITE_API_KEY
RUN npm run build

# Etapa 2: Servidor Nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]