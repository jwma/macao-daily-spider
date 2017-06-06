--任务表
create table macao_daily.task
(
	id int auto_increment
		primary key,
	url varchar(255) not null,
	extra_data text null,
	status int default '0' null
);