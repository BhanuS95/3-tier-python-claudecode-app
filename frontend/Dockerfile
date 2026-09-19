# ---------------------------------------------------------------------------
# Frontend Dockerfile - static HTML/CSS/JS served by Nginx
#
# Base image  : nginx:1.27-alpine (small, official)
# Port        : 3000
# User        : runs as the built-in unprivileged "nginx" user
# ---------------------------------------------------------------------------

FROM nginx:1.27-alpine

# Remove the default Nginx site and replace it with ours.
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY index.html /usr/share/nginx/html/index.html
COPY css /usr/share/nginx/html/css
COPY js /usr/share/nginx/html/js

# nginx:alpine already runs its worker processes as the "nginx" user;
# only the master process (which binds the port) starts as root, which
# is standard/required for the official image. File ownership is set
# explicitly for defense in depth.
RUN chown -R nginx:nginx /usr/share/nginx/html

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:3000/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
