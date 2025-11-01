# Docker possui instruções de instalação específicas para cada sistema operativo.
# Podemos consultar a documentação oficial no https://docker.com/get-started/
# Puxar ou extrair a imagem de Docker da Node.js:

docker pull node:24-alpine

# Criar um contentor de Node.js e iniciar uma sessão de Shell:

docker run -it --rm --entrypoint sh node:24-alpine

# Verify the Node.js version:

node -v # Should print "v24.11.0".

# Consultar a versão da npm:

npm -v # Deveria imprimir "11.6.1".