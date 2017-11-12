DROP TABLE attachment;
DROP TABLE mailitem;
DROP TABLE body;

CREATE TABLE body (
	id SERIAL PRIMARY KEY,
	sha256 text,
	content text
);

CREATE TABLE mailitem (
	id SERIAL PRIMARY KEY,
	dateSent date,
	subject text,
	bodyId integer REFERENCES body (id)
);

CREATE TABLE attachment (
	id SERIAL PRIMARY KEY,
	mailId integer REFERENCES mailitem (id),
	sha256 text,
	fileName text
);

