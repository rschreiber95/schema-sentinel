FROM node:22-alpine AS build

WORKDIR /app

COPY services/typescript/package.json services/typescript/package-lock.json ./
RUN npm ci

COPY services/typescript/tsconfig.json ./
COPY services/typescript/src ./src
RUN npm run build

FROM node:22-alpine

WORKDIR /app

COPY services/typescript/package.json services/typescript/package-lock.json ./
RUN npm ci --omit=dev

COPY --from=build /app/dist ./dist
COPY proto ./proto

CMD ["node", "dist/server.js"]
