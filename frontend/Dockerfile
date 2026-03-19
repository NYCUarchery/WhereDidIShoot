FROM node:22.12.0-alpine AS base

WORKDIR /app

RUN apk add --no-cache openjdk17-jre

COPY frontend/package.json frontend/package-lock.json frontend/openapitools.json ./frontend/

WORKDIR /app/frontend
RUN npm ci

FROM base AS dev

COPY frontend .
COPY backend/openapi.yml ../backend/openapi.yml

ENV NODE_ENV=development
ENV NUXT_TELEMETRY_DISABLED=1

EXPOSE 3000

CMD ["sh", "-c", "npm run generate:sdk && npm run dev"]

FROM base AS build

COPY frontend .
COPY backend/openapi.yml ../backend/openapi.yml
RUN npm run build

FROM node:20-alpine AS runtime

WORKDIR /app

ENV NODE_ENV=production
ENV NITRO_HOST=0.0.0.0
ENV NITRO_PORT=3000

COPY --from=build /app/frontend/.output ./.output

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
