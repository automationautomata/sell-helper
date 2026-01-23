FROM node:latest AS build
WORKDIR /app

COPY web-ui .
RUN npm install
RUN npm run build

FROM nginx:latest AS runtime

RUN rm -rf /usr/share/nginx/html/*

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
