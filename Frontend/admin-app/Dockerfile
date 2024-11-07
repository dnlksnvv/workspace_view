# Используем Node.js в качестве базового образа
FROM node:16

WORKDIR /admin-app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

FROM nginx:alpine
COPY --from=0 /admin-app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]