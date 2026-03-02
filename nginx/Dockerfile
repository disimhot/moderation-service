FROM nginx:1.27-alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom config
COPY nginx.conf /etc/nginx/conf.d/

# Copy static files
COPY static/ /usr/share/nginx/html/static/
COPY index.html /usr/share/nginx/html/
COPY 50x.html /usr/share/nginx/html/
