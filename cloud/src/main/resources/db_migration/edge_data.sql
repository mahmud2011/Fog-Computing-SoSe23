set SEARCH_PATH TO demo;
create table if not exists demo.edge_data
(
    data   jsonb not null,
    user_token_id integer,
    id            serial,
    constraint edge_data_pk
        primary key (id),
    constraint edge_data_user_token__fk
        foreign key (user_token_id) references demo.user_token (id)
);

