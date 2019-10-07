# v1.0.0
FROM golang:1.13.1 as build

COPY . /go/src/saodd

RUN cd /go/src/saodd && \
    go build -o register register.go

FROM alpine:latest

COPY --from=build /go/src/saodd/register /go/bin/register

# docker build -t registry.gitlab.com/saodd/saodd-github-io/register:v1.0 .
# docker push registry.gitlab.com/saodd/saodd-github-io/register:v1.0
# docker tag registry.gitlab.com/saodd/saodd-github-io/register:v1.0 registry.gitlab.com/saodd/saodd-github-io/register:latest
# docker push registry.gitlab.com/saodd/saodd-github-io/register:latest