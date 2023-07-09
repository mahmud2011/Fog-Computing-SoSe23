set SEARCH_PATH TO demo;
create table if not exists demo.user_token
(
    token varchar not null,
    id    serial
        constraint user_token_pk
            primary key
);

