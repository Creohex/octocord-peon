## About

This is a hobby project consisting of containerized discord and telegram clients.

These clients are meant for a limited list of private communities and offer both useful and completely useless commands, although can be used by anyone with some limitations.

So the main purposes of this project is to have fun, train various practices/technologies, and have a number of commands ready at the fingertips in the most popular messengers.


## Deploying

The easiest way would be to simply run:
> docker-compose build; docker-compose up

Be sure to add `.env` and `.db.env` files to the project root directory (or edit `docker-compose.yml`)

During start-up, all required environment variables will be listed.


## Extras

* `tools/import_guild_channels.sh` - Downloads all discord text channels of a specific guild in a json format. Requires a guild ID and a bot token which is authorized in that guild.
