# Etapa 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Etapa 2: Servindo build
FROM node:20-alpine as runner

WORKDIR /app

# Instalar 'serve' para entregar os arquivos estáticos
RUN npm install -g serve

COPY --from=builder /app/dist ./dist

# Railway expõe PORT dinamicamente
ENV PORT=3000

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
