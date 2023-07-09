set SEARCH_PATH TO demo;
create table if not exists demo.config
(
    data          jsonb not null,
    id            serial
        constraint config_pk
            primary key,
    edge_data_id integer
        constraint config_edge_data_id_fk
            references demo.edge_data
);

