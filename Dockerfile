#FROM registry.gitlab.com/saodd/saodd-github-io/register:latest as register
FROM registry.gitlab.com/saodd/saodd-github-io/register:latest as register

FROM nginx:1.17.4

COPY --from=register    /go/bin/register    /usr/share/nginx/html/register/register
COPY                    ./static/blog       /usr/share/nginx/html/static/blog
COPY                    ./_posts            /usr/share/nginx/html/static/posts

CMD /usr/share/nginx/html/register/register && nginx -g "daemon off;"