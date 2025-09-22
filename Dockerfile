FROM python:3.11-alpine AS builder

RUN pip install jinja2

WORKDIR /build

COPY server/nginx.conf.j2 /build/nginx.conf.j2
COPY wallets-v2.json /build/wallets-v2.json
COPY wallets.json /build/wallets.json
COPY scripts/proxy_urls.py /build/proxy_urls.py
COPY scripts/generate_nginx_conf.py /build/generate_nginx_conf.py

ARG ASSETS_PREFIX=assets
ARG SERVER_NAME=config.ton.org
ARG CACHE_DURATION_OK=10m
ARG CACHE_DURATION_NOTOK=2m

RUN python proxy_urls.py \
    --input wallets-v2.json \
    --output wallets-v2.proxy.json \
    --origins origins.json \
    --base-url "https://${SERVER_NAME}/${ASSETS_PREFIX}/"

RUN python generate_nginx_conf.py \
    --template nginx.conf.j2 \
    --origins origins.json \
    --output nginx.conf \
    --assets-prefix "${ASSETS_PREFIX}" \
    --server-name "${SERVER_NAME}" \
    --cache-duration-ok "${CACHE_DURATION_OK}" \
    --cache-duration-notok "${CACHE_DURATION_NOTOK}"

FROM nginx:alpine

ARG ASSETS_PREFIX=assets

COPY --from=builder /build/nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /build/wallets-v2.proxy.json /usr/share/nginx/html/wallets-v2.json
COPY --from=builder /build/wallets.json /usr/share/nginx/html/wallets.json
COPY assets/ /var/www/predownloaded_images/${ASSETS_PREFIX}/

RUN mkdir -p /var/cache/nginx/image_cache && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/www/predownloaded_images

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
