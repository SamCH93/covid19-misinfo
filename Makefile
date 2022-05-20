all: dbuild drun

## build docker image (requires root access for docker)
dbuild: Dockerfile
	docker build \
    -t covidmisinfo .

## run docker image that produces tex from within docker
drun: dbuild
	docker run \
    --rm \
	-it \
	-v $(CURDIR):/host \
	-p 8889:8889 \
	covidmisinfo
