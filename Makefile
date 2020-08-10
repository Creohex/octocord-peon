
info:
	 @echo "Existing targets"
	 @echo "   li - run linter
	 @echo "   test - run tests"
	 @echo "   build docker images"
	 @echo "   run - run docker-compose"
	 @echo "   stop - stop docker-compose"
	 @echo "   attach <name> - attach to running container"

li:
	# TODO: ...
	 ./lint ./*

build:
	 docker-compose build

run:
	 docker-compose -d up

stop:
	 docker-compose stop

attach:
	 # TODO: ...
	 @echo attach...

test:
	 # TODO: ...
	 @echo tests...
