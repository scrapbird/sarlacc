# Sarlacc

This is an SMTP server that I use in my malware lab to collect spam from infected hosts.

It will collect all mail items sent to it in a postgres database, storing all attachments in mongodb.

This is work in progress code and there will probably be bugs but it does everything I need.


## Getting Started

To get started with docker-compose, simply run `docker-compose up`. If installing in a production environment, an install of mongodb and postgresql will be required and sarlacc can be configured via the config file in `smtpd/src/smtpd.cfg`.

Once the docker containers are running, the postgres database will need to be initialized and permissions granted to the user to access the database:
```
psql -h localhost -U postgres < postgres_init.sql
psql -h localhost -U postgres -d sarlacc < postgres_grant.sql
```

If you want to use different credentials (you should) then modify the postgres_init.sql, postgres_grant.sql and the config file for the smtp server appropriately.

### Requirements

python3.5


## Web Client

The web client has not been built yet, to view the data you will need to manually interact with the databases.


## Plugins

You can extend sarlacc via plugins. Simply drop a python file into `smtp/src/plugins`. There is an example plugin at `smtp/src/plugins/example.py`.
