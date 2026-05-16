FROM node:20

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm --version \
    && npm config set registry https://registry.npmjs.org/ \
    && npm install --no-audit --no-fund --progress=true --loglevel=verbose

COPY . .

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
