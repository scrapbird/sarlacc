# Sarlacc

This is an SMTP server that I use in my malware lab to collect spam from infected hosts.

It will collect all mail items sent to it in a postgres database, storing all attachments in mongodb.

This is work in progress code and there will probably be bugs but it does everything I need.

Warning: There will most likely be breaking changes as I flesh out the plugin API. Once it has stabilized I will give this a version number and try not to break anything else.


## Getting Started

### docker-compose

To get started with docker-compose, simply run `docker-compose up`.

The server will then be listening for SMTP connections on port `2500`.

#### Data
To ensure proper data persistence, data for both postgres and mongodb is stored in docker volumes.


### Production

If installing in a production environment which requires a proper setup, an install of mongodb and postgresql will be required.
To configure sarlacc, copy the default config file to `smtpd/src/smtpd.cfg` and override the settings you wish to change:
```
cp smtpd/src/smtpd.cfg.default smtpd/src/smtpd.cfg
$EDITOR smtpd/src/smtpd.cfg
```
Then edit the file with your required configuration.

You can use the `postgres/postgres_init.sql` script to initialize the database for use with sarlacc.
```
psql -h localhost -U postgres < postgres/postgres_init.sql
```

If you want to use different credentials (you should) then modify the `postgres/postgres_init.sql` and the config file for the smtp server appropriately.

cd into the `smtpd/src` directory:
```
cd smtpd/src
```

Install the dependencies:
```
pip install -r requirements.txt
```

Start the server:
```
./app.py
```

The server will then be listening for SMTP connections on port `2500`.


### Requirements

python3.5



## Web Client

The web client has not been built yet, to view the data you will need to manually interact with the databases.



## Plugins

You can extend sarlacc via plugins. Simply drop a python file (or a directory with an __init__.py file) into `smtpd/src/plugins`. There are example's of both types of plugins at `smtpd/src/plugins/example.py` and `smtpd/src/plugins/directory_example`.

To get a full idea of what events are available for the plugins to be notified by, check out the `smtpd/src/plugins/plugin.py` file.

Plugins are also exposed to the internal storage API, from which you can pull email items, recipients, attachments, tag attachments etc etc. Take a look at the `smtpd/src/storage.py` file for more info on how to use this.
