## About

This is a hobby project consisting of containerized discord and telegram clients.

These clients are meant for a number of private communities and offer both useful and completely useless functionality, although anyone is welcome to use it.

The main purpose of this project is to have fun, train various practices/technologies, and have a number of commands ready at the fingertips in the most popular messengers.


## Deploying

The easiest way would be to simply run:
> docker-compose build; docker-compose up

Be sure to add `.env` and `.db.env` files to the project root directory (or edit `docker-compose.yml`)

During start-up, all required environment variables will be listed.
