# Serves the static site built by `make site` (dist/web) with nginx.
#   make site
#   docker build -t synthride .
#   docker run --rm -p 8080:80 synthride    # then open http://127.0.0.1:8080
FROM nginx:1.27-alpine

COPY dist/web/ /usr/share/nginx/html/
