DROP TABLE attachment;
DROP TABLE body;
DROP TABLE mailitem;

CREATE TABLE mailitem (
	id SERIAL PRIMARY KEY,
	dateSent date,
	subject text
);

CREATE TABLE body (
	id SERIAL PRIMARY KEY,
	mailId integer REFERENCES mailitem (id),
	sha256 text,
	content text
);

CREATE TABLE attachment (
	id SERIAL PRIMARY KEY,
	mailId integer REFERENCES mailitem (id),
	sha256 text,
	fileName text
);

