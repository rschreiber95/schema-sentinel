FROM node:22-alpine AS build
WORKDIR /app/runtimes/typescript
COPY runtimes/typescript/package*.json ./
RUN npm ci
COPY runtimes/typescript/main.ts runtimes/typescript/tsconfig.json ./
COPY generated/ts /app/generated/ts
RUN npm run build
FROM node:22-alpine
WORKDIR /app/runtimes/typescript
COPY runtimes/typescript/package*.json ./
RUN npm ci --omit=dev
COPY --from=build /app/runtimes/typescript/dist ./dist
CMD ["node", "dist/runtimes/typescript/main.js", "--serve"]
