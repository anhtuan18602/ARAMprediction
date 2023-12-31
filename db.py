import sqlite3
import json
from pathlib import Path
from datetime import datetime as dt

import pandas as pd
from riot import *
from log import get_log


log = get_log(__name__)


class Database():
    __slots__ = ("db_path", "sql_path", "cxn", "cur")

    def __init__(self, db_path: Path, build_path: Path) -> None:
        self.db_path = (db_path / 'league.db').resolve()
        self.sql_path = (build_path / 'league.sql').resolve()

    def connect(self):
        self.cxn = sqlite3.connect(self.db_path, check_same_thread=False)
        log.info(f"Connected to database at {self.db_path}")
        self.cur = self.cxn.cursor()
        self.build()

    def build(self):
        self.scriptexec(self.sql_path)
        self.commit()
        log.info(f"Built database ({self.db_path.parts[-1]})")

    def commit(self):
        self.cxn.commit()

    def close(self):
        self.cxn.commit()
        self.cxn.close()
        log.info("Closed database connection")

    def record(self, command: str, *values):
        self.cur.execute(command, tuple(values))

        return self.cur.fetchone()

    def records(self, command, *values):
        self.cur.execute(command, tuple(values))

        return self.cur.fetchall()

    def column(self, table: str):
        self.cur.execute(f"PRAGMA table_info({table});")

        return [item[1] for item in self.cur.fetchall()]

    def execute(self, command, *values):
        self.cur.execute(command, tuple(values))

    def scriptexec(self, path: Path | str):
        if not isinstance(path, Path):
            path = Path(path)
        path = path.resolve()

        with open(path, 'r', encoding="utf-8") as script:
            self.cur.executescript(script.read())
            log.info(f"Executed script query from {path}")

    # TODO: LOAD
    def add_summoner(self, puuid: str, name: str, region: str):
        """
        Add summoner
        """
        query = self.record("SELECT * FROM summoners where s_id = (?)", puuid)
        if not query:
            url = f"https://www.op.gg/summoners/vn/{name.replace(' ', '%20')}"
            self.execute("INSERT INTO summoners VALUES (?, ?, ?, ?)",
                         puuid, name, region, url)
            self.commit()
        else:
            log.warning("Summoner already existed")

    def add_matches(self, df: pd.DataFrame):
        """
        Add matches of summoner
        """
        for i in range(len(df)):
            id = "VN2_" + str(df['gameId'][i])
            query = self.record("SELECT * FROM matches where m_id = (?)", id)
            if not query:
                timestamp = df['gameCreation'][i]
                date = dt.fromtimestamp(
                    timestamp/1000).strftime("%Y-%m-%d %H:%M:%S")
                duration = int(df['gameDuration'][i])
                self.execute("INSERT INTO matches VALUES (?, ?, ?)",
                             id, date, duration)
                self.commit()

    def add_stats(self, puuid: str, match_ids: str, player_df: pd.DataFrame):
        """
        Add performance statistics
        """
        player = player_df.to_dict(orient='records')
        for i in range(len(player)):
            query = self.record(
                "SELECT * FROM performs WHERE s_id = (?) and m_id = (?)", puuid, match_ids[i])
            if not query:
                self.execute("INSERT INTO performs VALUES (?, ?, ?)",
                             puuid, match_ids[i],  json.dumps(player[i]))
                self.commit()

    # TO be removed
    def add_training(self, match_id, stats_list, label):

        query = self.record("SELECT * FROM training where m_id = (?)", match_id)
        if not query:
            columns = [match_id]
            columns.extend(stats_list)
            columns.append(label)
            placeholders = ','.join(["?" for _ in columns])
            self.execute(f"INSERT INTO training VALUES ({placeholders})",
                        *columns)
            self.commit()


    def add_tags(self, match_id, allies, enemies, nof_tags):

        query = self.record("SELECT * FROM tags where m_id = (?)", match_id)
        if not query:
            columns = [match_id]
            columns.extend(allies)
            columns.extend(enemies)
            print(columns)
            placeholders = ', '.join(["?" for _ in range(nof_tags*2+1)])
            self.execute(
            f"INSERT INTO tags VALUES ({placeholders}) ",
                        *columns)
            self.commit()


    def get_trainings(self, columns):
        print(f"SELECT {', '.join([column for column in columns])}, m_win FROM training ")
        query = self.records(f"SELECT {', '.join([column for column in columns])}, m_win FROM training ")
        if not query:
            log.info("Can't get training data")
            return None
        else:
            features = []
            for row in query:
                features.append(list(row))

        return pd.DataFrame(features, columns=(columns+["target"]))

    def get_model_data(self, ratio_columns, tags_columns):
        ratio_placeholder = ', '.join([("training." + column) for column in ratio_columns])
        if tags_columns:
            tags_placeholder = ', '.join([("tags." + column) for column in tags_columns])
            statement = (
            #f"SELECT {ratio_placeholder},matches.m_duration, training.m_win " +
            f"SELECT {ratio_placeholder},{tags_placeholder}, training.m_win " +
            "FROM training " +
            "INNER JOIN tags " +
            "ON training.m_id = tags.m_id "
            )
        else:
            statement = (
            #f"SELECT {ratio_placeholder},matches.m_duration, training.m_win " +
            f"SELECT {ratio_placeholder}, training.m_win " +
            "FROM training "
            )
        query = self.records(statement)
        if not query:
            log.info("Can't get data")
            return None
        else:
            features = []
            for row in query:
                features.append(list(row))
        if tags_columns:
            return pd.DataFrame(features, columns=(ratio_columns + tags_columns + ["target"]))
        else:
            return pd.DataFrame(features, columns=(ratio_columns + ["target"]))





    # TODO: EXTRACT
    # The query params are modified to be optional
    def get_stats(self, puuid=None, match_id=None) -> pd.DataFrame:
        statement = "SELECT * FROM performs "
        values = []
        if puuid:
            statement += "WHERE s_id = (?) "
            values.append(puuid)
        if match_id:
            statement += "WHERE m_id = (?)"
            values.append(match_id)
        query = self.records(statement, *values)
        if not query:
            log.info("Stats does not exist")
            return None
        else:
            load = []
            for row in query:
                load.append(json.loads(row[2]))
        return pd.json_normalize(load)


    def get_stat(self, puuid: str, match_id: str) -> pd.DataFrame:

        query = self.record(
            "SELECT * FROM performs WHERE s_id = (?) and m_id = (?)", puuid, match_id)
        if not query:
            log.info("Stats does not exist")
            return None
        else:
            load = json.loads(query[2])
        return pd.json_normalize(load)


    def get_matches(self):
        statement = (
            "SELECT m_id FROM matches " +
            "WHERE m_id NOT IN " +
            "(SELECT m_id from training) " +
            "AND m_id NOT IN " +
            "(SELECT m_id from tags)"
        )

        query = self.records(statement)
        if not query:
            log.info("Cannot get matches")
            return None
        else:
            load = []
            for match in query:
                load.append(match[0])
        return load


    def delete_match(self, match_id):
        self.execute("DELETE FROM matches WHERE m_id = (?)", match_id)
        self.commit()


def init_database():
    db_path = Path(".")
    build_path = Path(".")

    db = Database(db_path, build_path)
    db.connect()
    return db


def update_database(db, summoner_name,
                    api_key="RGAPI-a384a673-d288-42ec-a860-55a1602dba94",
                    region='vn2', mass_region='sea', no_games=5, queue_id=450) -> pd.DataFrame:
    # TODO: EXTRACT (For each summoner)
    puuid = get_puuid(summoner_name, region, api_key)
    match_ids = get_match_ids(puuid, mass_region, no_games, queue_id, api_key)
    games, player = gather_data(puuid, match_ids, mass_region, api_key)

    # TODO: LOAD
    db.add_matches(games)
    db.add_summoner(puuid, summoner_name, region)
    db.add_stats(puuid, match_ids, player)

    stats = transform(games, player)
    return stats


if __name__ == "__main__":
    db = init_database()
    members = ['Cozy Bearrrrr',
               'UnbeatableVN',
               '3 Giờ Rửa Chim',
               'Lushen2711',
               'Sứ Giả Lọk Khe',
               'Wavepin']
    for member in members:
        df = update_database(db=db, summoner_name=member)
