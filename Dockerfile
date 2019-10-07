FROM registry.gitlab.com/saodd/saodd-github-io/register:latest as register

FROM nginx:1.16.1-alpine

COPY --from=register    /go/bin/register    /go/bin/register
COPY                    ./static/blog       /usr/share/nginx/html/static/blog
COPY                    ./_posts            /usr/share/nginx/html/posts

CMD /go/bin/register && nginx -g "daemon off;"