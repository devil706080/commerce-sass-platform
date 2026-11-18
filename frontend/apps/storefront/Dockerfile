FROM node:26-alpine AS dependencies
WORKDIR /workspace
RUN npm install --global pnpm@12.19.0
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/storefront/package.json ./apps/storefront/package.json
RUN pnpm install --frozen-lockfile --filter @commerce-saas/storefront...

FROM node:26-alpine AS build
WORKDIR /workspace
ARG NEXT_PUBLIC_KEYCLOAK_URL
ARG NEXT_PUBLIC_KEYCLOAK_REALM
ARG NEXT_PUBLIC_KEYCLOAK_CLIENT_ID
ENV NEXT_PUBLIC_KEYCLOAK_URL=$NEXT_PUBLIC_KEYCLOAK_URL \
    NEXT_PUBLIC_KEYCLOAK_REALM=$NEXT_PUBLIC_KEYCLOAK_REALM \
    NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=$NEXT_PUBLIC_KEYCLOAK_CLIENT_ID
RUN npm install --global pnpm@12.19.0
COPY --from=dependencies /workspace/node_modules ./node_modules
COPY --from=dependencies /workspace/apps/storefront/node_modules ./apps/storefront/node_modules
COPY . .
RUN pnpm --filter @commerce-saas/storefront typecheck && pnpm --filter @commerce-saas/storefront build

FROM gcr.io/distroless/nodejs24-debian12:nonroot AS runtime
WORKDIR /app
ENV NODE_ENV=production HOSTNAME=0.0.0.0 PORT=3002
COPY --from=build --chown=nonroot:nonroot /workspace/apps/storefront/.next/standalone ./
COPY --from=build --chown=nonroot:nonroot /workspace/apps/storefront/.next/static ./apps/storefront/.next/static
EXPOSE 3002
CMD ["apps/storefront/server.js"]
