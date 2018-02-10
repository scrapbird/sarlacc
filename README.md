# Sarlacc

This is an SMTP server that I use in my malware lab to collect spam from infected hosts.

It will collect all mail items sent to it in a postgres database, storing all attachments in mongodb.

This is work in progress code and there will probably be bugs but it does everything I need.


## Getting Started

### docker-compose

To get started with docker-compose, simply run `docker-compose up`.

Once the docker containers are running, the postgres database will need to be initialized and permissions granted to the user to access the database:
```
psql -h localhost -U postgres < postgres_init.sql
psql -h localhost -U postgres -d sarlacc < postgres_grant.sql
```

The server will then be listening for SMTP connections on port `2500`.


### Production

If installing in a production environment which requires a proper setup, an install of mongodb and postgresql will be required.
To configure sarlacc, copy the default config file to `smtpd/src/smtpd.cfg` and onverride the settings you wish to change:
```
cp smtpd/src/smtpd.cfg.default smtpd/src/smtpd.cfg
$EDITOR smtpd/src/smtpd.cfg
```
Then edit the file with your required configuration. You can use the `postgres_init.sql` and `postgres_grant.sql` scripts as detailed in the [docker-compose](#docker-compose) section above to intitialize the database for use with sarlacc (yeah one day I'll get around to doing that automatically).


If you want to use different credentials (you should) then modify the `postgres_init.sql`, `postgres_grant.sql` and the config file for the smtp server appropriately.

The server will then be listening for SMTP connections on port `2500`.


### Data
Data for both postgres and mongodb is stored by docker in the `data` directory, keep this here if you want to keep data from previous sessions.


### Requirements

python3.5



## Web Client

The web client has not been built yet, to view the data you will need to manually interact with the databases.



## Plugins

You can extend sarlacc via plugins. Simply drop a python file into `smtp/src/plugins`. There is an example plugin at `smtp/src/plugins/example.py`.
