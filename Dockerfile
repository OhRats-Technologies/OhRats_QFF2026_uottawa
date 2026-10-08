FROM nginx:1.28-alpine

COPY deploy/fireline/nginx.conf /etc/nginx/conf.d/default.conf
COPY web/demo/ /usr/share/nginx/html/
COPY web/presentation/ /usr/share/nginx/html/presentation/

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/healthz || exit 1
