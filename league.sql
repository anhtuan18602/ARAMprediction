create table
    if not exists summoners (
        s_id text PRIMARY KEY, -- Summoner puuid
        s_name text not null, -- Summoner name
        s_region text not null, -- Summoner region
        s_url text not null -- Summoner opgg url
    );

create table
    if not exists matches (
        m_id text PRIMARY KEY, -- Match id
        m_date text not null, -- Match date
        m_duration integer not null -- Match duration (ms)
    );

create table
    if not exists training (
        m_id text PRIMARY KEY,
        m_winrate float not null,
        m_kda float not null,
        m_dmg float not null,
        m_nof_games integer not null,
        m_mastery integer not null,
        m_win integer not null
    );


create table
    if not exists mastery (
      m_id text PRIMARY KEY,
      m_mastery integer not null
    );


create table
    if not exists tags (
        m_id text PRIMARY KEY,
        a_mage integer not null,
        a_marksman integer not null,
        a_tank integer not null,
        a_assassin integer not null,
        a_support integer not null,
        a_fighter integer not null,
        e_mage integer not null,
        e_marksman integer not null,
        e_tank integer not null,
        e_assassin integer not null,
        e_support integer not null,
        e_fighter integer not null
    );

create table
    if not exists performs (
        s_id text not null, -- Summoner id
        m_id text not null, -- Match id
        p_stats blob not null, -- Summoner performance (json)
        PRIMARY KEY (s_id, m_id),
        FOREIGN KEY (s_id) REFERENCES summoners (s_id) ON DELETE CASCADE,
        FOREIGN KEY (m_id) REFERENCES matches (m_id) ON DELETE CASCADE
    );
