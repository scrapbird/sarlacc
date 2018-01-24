\connect sarlacc

CREATE ROLE "user";

DROP TABLE attachment CASCADE;
DROP TABLE recipient CASCADE;
DROP TABLE mailrecipient CASCADE;
DROP TABLE mailitem CASCADE;
DROP TABLE body CASCADE;

CREATE TABLE body (
	id SERIAL PRIMARY KEY,
	sha256 text,
	content text
);

CREATE TABLE mailitem (
	id SERIAL PRIMARY KEY,
	datesent date,
	subject text,
	fromaddress text,
	bodyid integer REFERENCES body (id)
);

CREATE TABLE recipient (
	id SERIAL PRIMARY KEY,
	emailaddress text
);

CREATE TABLE mailrecipient (
	id SERIAL PRIMARY KEY,
	recipientid integer REFERENCES recipient (id),
	mailid integer REFERENCES mailitem (id)
);

CREATE TABLE attachment (
	id SERIAL PRIMARY KEY,
	mailid integer REFERENCES mailitem (id),
	sha256 text,
	filename text
);

