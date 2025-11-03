# ==============================
# Etapa 1: Build
# ==============================
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . .
RUN npm run build

# ==============================
# Etapa 2: Execução
# ==============================
FROM node:20-alpine AS runner

WORKDIR /app

# Copia o código buildado e dependências
COPY --from=builder /app /app

# Instala TODAS as dependências (incluindo vite)
RUN npm install

# Porta padrão do Vite Preview
EXPOSE 4173

# Executa o preview com host liberado
CMD ["npm", "run", "preview", "--", "--host", "--port", "4173"]
# docker build -t pulso-frontend .
# docker run -d -p 4173:4173 pulso-frontend
# docker system prune -af