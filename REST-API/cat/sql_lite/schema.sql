CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL, 
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
CREATE TABLE team (
	teamname VARCHAR(200) NOT NULL, 
	email VARCHAR(200), 
	mswebhook VARCHAR(500), 
	PRIMARY KEY (teamname)
);
CREATE TABLE product (
	productname VARCHAR(200) NOT NULL, 
	strategy VARCHAR(10), 
	max_days INTEGER, 
	max_days_month INTEGER, 
	case_regex VARCHAR(200), 
	quota_over_days INTEGER, 
	sf_api VARCHAR(2000), 
	sf_job_cron VARCHAR(200), 
	sf_job_timezone VARCHAR(200), 
	sf_job_query_interval INTEGER, 
	PRIMARY KEY (productname)
);
CREATE TABLE user (
	id INTEGER NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	email VARCHAR(100), 
	password VARCHAR(200) NOT NULL, 
	user_since DATETIME NOT NULL, 
	teamname VARCHAR(200) NOT NULL, 
	active BOOLEAN, 
	shift_start VARCHAR(100) NOT NULL, 
	shift_end VARCHAR(100) NOT NULL, 
	first_name VARCHAR(50) NOT NULL, 
	last_name VARCHAR(50) NOT NULL, 
	timezone VARCHAR(200) NOT NULL, 
	last_login DATETIME NOT NULL, 
	admin BOOLEAN, 
	team_email_notifications BOOLEAN, 
	monitor_case_updates BOOLEAN,
	PRIMARY KEY (id), 
	UNIQUE (username), 
	FOREIGN KEY(teamname) REFERENCES team (teamname)
);
CREATE TABLE salesforce_cases (
	id INTEGER NOT NULL, 
	case_id VARCHAR(50), 
	product VARCHAR(200) NOT NULL, 
	priority VARCHAR(10), 
	time DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (case_id), 
	FOREIGN KEY(product) REFERENCES product (productname)
);
CREATE TABLE user_product (
	user_name VARCHAR(50) NOT NULL, 
	product_name VARCHAR(200) NOT NULL, 
	active BOOLEAN, 
	quota INTEGER, 
	PRIMARY KEY (user_name, product_name), 
	FOREIGN KEY(user_name) REFERENCES user (username), 
	FOREIGN KEY(product_name) REFERENCES product (productname)
);
CREATE TABLE jobs (
	number INTEGER NOT NULL, 
	id VARCHAR(200), 
	username VARCHAR(50), 
	job_type VARCHAR(100), 
	details VARCHAR(500), 
	time DATETIME NOT NULL, 
	status VARCHAR(100), 
	PRIMARY KEY (number), 
	FOREIGN KEY(username) REFERENCES user (username) ON DELETE SET NULL
);
CREATE TABLE audit (
	id INTEGER NOT NULL, 
	user VARCHAR(50), 
	task_type VARCHAR(100), 
	task VARCHAR(5000), 
	time DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user) REFERENCES user (username) ON DELETE SET NULL
);
CREATE TABLE salesforce_emails (
	id INTEGER NOT NULL, 
	user VARCHAR(50), 
	email_name VARCHAR(200) NOT NULL, 
	email_body VARCHAR(5000), 
	email_subject VARCHAR(500), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user) REFERENCES user (username), 
	UNIQUE (email_name)
);
CREATE TABLE cases (
	id VARCHAR(50) NOT NULL, 
	user VARCHAR(50) NOT NULL, 
	product VARCHAR(200) NOT NULL, 
	time DATETIME NOT NULL, 
	comments VARCHAR(300), 
	mode VARCHAR(50), 
	priority VARCHAR(10), 
	assigned_by VARCHAR(50), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user) REFERENCES user (username), 
	FOREIGN KEY(product) REFERENCES product (productname), 
	FOREIGN KEY(assigned_by) REFERENCES user (username) ON DELETE SET DEFAULT
);
