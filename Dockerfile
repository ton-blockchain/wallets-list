FROM python:3.11-alpine AS builder

WORKDIR /build

COPY server/nginx.conf /build/nginx.conf
COPY wallets-v2.json /build/wallets-v2.json
COPY wallets.json /build/wallets.json
COPY scripts/proxy_urls.py /build/proxy_urls.py

ARG SERVER_NAME=config.ton.org

RUN python proxy_urls.py \
    --input wallets-v2.json \
    --output wallets-v2.proxy.json \
    --base-url "https://${SERVER_NAME}/assets/"

FROM nginx:alpine

RUN rm /usr/share/nginx/html/*

COPY --from=builder /build/nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /build/wallets-v2.proxy.json /usr/share/nginx/html/wallets-v2.json
COPY --from=builder /build/wallets.json /usr/share/nginx/html/wallets.json
COPY assets/ /usr/share/nginx/html/assets/


EXPOSE 80

CMD nginx -g "daemon off;"
