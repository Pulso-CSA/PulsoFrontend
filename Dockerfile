# Etapa 1: Build
FROM node:20-alpine AS builder

# Define diretório de trabalho
WORKDIR /app

# Copia apenas os arquivos essenciais primeiro (para otimizar cache)
COPY package*.json ./

# Instala dependências (usa npm ci se houver package-lock.json)
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# Copia o restante do código
COPY . .

# Compila o código TypeScript (se houver script de build)
RUN if npm run | grep -q "build"; then npm run build; else echo "Nenhum build encontrado (usando npm run dev direto)"; fi


# Etapa 2: Execução
FROM node:20-alpine

WORKDIR /app

# Copia apenas o necessário da etapa de build
COPY --from=builder /app ./

# Exponha a porta usada pelo app (ajuste conforme necessário)
EXPOSE 3000

# Comando de inicialização
CMD ["npm", "run", "dev"]
