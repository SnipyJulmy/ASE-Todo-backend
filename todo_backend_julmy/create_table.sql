-- DROP TABLE
drop table main.tags;
drop table main.todos;
drop table main.assoc;

-- CREATE TABLE
create table if not exists main.tags (
  id   integer primary key,
  title char(10) not null
);

create table if not exists main.todos (
  id        integer primary key,
  title     char(50) not null,
  completed boolean  not null,
  t_order   integer  not null
);

create table if not exists main.assoc (
  tag_id  integer not null,
  todo_id integer not null,
  primary key (tag_id, todo_id)
)