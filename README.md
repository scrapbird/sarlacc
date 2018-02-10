# Sarlacc

This is an SMTP server that I use in my malware lab to collect spam from infected hosts.

It will collect all mail items sent to it in a postgres database, storing all attachments in mongodb.

This is work in progress code and there will probably be bugs but it does everything I need.


## Getting Started

### docker-compose

To get started with docker-compose, simply run `docker-compose up`.

The server will then be listening for SMTP connections on port `2500`.

#### Data
To ensure proper data persistence, data for both postgres and mongodb is stored in docker volumes.


### Production

If installing in a production environment which requires a proper setup, an install of mongodb and postgresql will be required.
To configure sarlacc, copy the default config file to `smtpd/src/smtpd.cfg` and onverride the settings you wish to change:
```
cp smtpd/src/smtpd.cfg.default smtpd/src/smtpd.cfg
$EDITOR smtpd/src/smtpd.cfg
```
Then edit the file with your required configuration.

You can use the `postgres/postgres_init.sql` script to intitialize the database for use with sarlacc.
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

You can extend sarlacc via plugins. Simply drop a python file into `smtp/src/plugins`. There is an example plugin at `smtp/src/plugins/example.py`.
