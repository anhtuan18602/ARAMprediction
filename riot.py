import requests
from tqdm import tqdm
import time
import pandas as pd
import asyncio

def get_puuid(summoner_name, region, api_key):
    api_url = (
        "https://" +
        region +
        ".api.riotgames.com/lol/summoner/v4/summoners/by-name/" +
        summoner_name +
        "?api_key=" +
        api_key
    )
    resp = requests.get(api_url)
    player_info = resp.json()
    puuid = player_info['puuid']
    return puuid


def get_summonerid(summoner_name, region, api_key):
    api_url = (
        "https://" +
        region +
        ".api.riotgames.com/lol/summoner/v4/summoners/by-name/" +
        summoner_name +
        "?api_key=" +
        api_key
    )
    resp = requests.get(api_url)
    player_info = resp.json()
    id = player_info['id']
    return id


def get_summoner_name(summoner_id, region, api_key):
    api_url = (
        "https://" +
        region +
        ".api.riotgames.com/lol/summoner/v4/summoners/" +
        summoner_id +
        "?api_key=" +
        api_key
    )
    while True:
        resp = requests.get(api_url)

        if resp.status_code == 429:
            print("Rate Limit hit, sleeping for 10 seconds")
            time.sleep(10)
            # continue means start the loop again
            continue

        player_info = resp.json()
        name = player_info['name']
        return name


def get_match_ids(puuid, mass_region, no_games, queue_id, api_key):
    api_url = (
        "https://" +
        mass_region +
        ".api.riotgames.com/lol/match/v5/matches/by-puuid/" +
        puuid +
        "/ids?start=0" +
        "&count=" +
        str(no_games) +
        "&queue=" +
        str(queue_id) +
        "&api_key=" +
        api_key
    )

    print(f"REQUEST URL: {api_url}")

    resp = requests.get(api_url)
    match_ids = resp.json()
    return match_ids


def get_match_data(match_id, mass_region, api_key):
    api_url = (
        "https://" +
        mass_region +
        ".api.riotgames.com/lol/match/v5/matches/" +
        match_id +
        "?api_key=" +
        api_key
    )

    # we need to add this "while" statement so that we continuously loop until it's successful
    while True:
        resp = requests.get(api_url)

        if resp.status_code == 429:
            print("Rate Limit hit, sleeping for 10 seconds")
            time.sleep(10)
            # continue means start the loop again
            continue

        match_data = resp.json()
        return match_data


def find_player_data(match_data, puuid):
    participants = match_data['metadata']['participants']
    player_index = participants.index(puuid)
    player_data = match_data['info']['participants'][player_index]
    return player_data


def gather_data(puuid, match_ids, mass_region, api_key):
    matches = []
    player = []
    for match_id in tqdm(match_ids):
        match_data = get_match_data(match_id, mass_region, api_key)
        player_data = find_player_data(match_data, puuid)
        matches.append(match_data['info'])
        player.append(player_data)

    # Dataframe of all players of 5 games (5 x 10 records)
    df = pd.json_normalize(matches)
    # Dataframe of player of 5 games
    player_df = pd.json_normalize(player)
    return df, player_df


def progress_bar(percent: float) -> str:
    progress = ''
    for i in range(12):
        if i == (int)(percent*12):
            progress += '🔘'
        else:
            progress += '▬'
    return progress


def transform(df: pd.DataFrame, player_df: pd.DataFrame):
    stats = {}
    # KDA
    stats['kills'] = player_df['kills'].mean()
    stats['deaths'] = player_df['deaths'].mean()
    stats['assists'] = player_df['assists'].mean()

    # Champions
    stats['champions'] = player_df['championName'].tolist()

    # Damage, Penta, Games
    stats['dmg'] = player_df['totalDamageDealtToChampions'].mean()  # Dmg
    stats['penta'] = player_df['pentaKills'].sum()  # Penta
    stats['wins'] = player_df['win'].value_counts().values[0]  # Wins
    stats['loses'] = player_df['win'].value_counts().values[1]  # Loses

    # Achievements (time in sec)
    stats['duration'] = df['gameDuration'].mean()//60
    stats['timealive'] = player_df['longestTimeSpentLiving'].mean()
    stats['timedead'] = player_df['totalTimeSpentDead'].mean()
    stats['totalheal'] = player_df['totalHealsOnTeammates'].mean()
    stats['cs'] = player_df['totalMinionsKilled'].mean()
    stats['cspermin'] = round(stats['cs']/stats['duration'], 2)

    if stats['timealive'] > stats['timedead']:
        stats['badge'] = "🛡️ Guardian Angel"
    else:
        stats['badge'] = "💀 Death's Dance"
    return stats



def get_current_match(summoner_id, region, api_key):
    api_url = (
        "https://" +
        region +
        ".api.riotgames.com/lol/spectator/v4/active-games/by-summoner/" +
        summoner_id +
        "?api_key=" +
        api_key
    )
    while True:
        resp = requests.get(api_url)

        if resp.status_code == 429:
            print("Rate Limit hit, sleeping for 10 seconds")
            time.sleep(10)
            # continue means start the loop again
            continue

        match_data = resp.json()
        return match_data


def get_mastery(summoner_id, champion_id, region, api_key):
    api_url = (
        "https://" +
        region +
        ".api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/" +
        summoner_id +
        "/by-champion/" +
        str(champion_id) +
        "?api_key=" +
        api_key
    )
    while True:
        resp = requests.get(api_url)
        if resp.status_code != 200:
            print("Not found")
            return {"championPoints": 0}
        if resp.status_code == 429:
            print("Rate Limit hit, sleeping for 10 seconds")
            time.sleep(10)
            # continue means start the loop again
            continue

        mastery = resp.json()
        return mastery

def get_participants_info(match_data, region, api_key):

    participants = []
    for participant in match_data['participants']:
        name = get_summoner_name(participant["summonerId"], region, api_key)
        participants.append({
        "champion_id": participant["championId"],
        "summoner_name": name,
        "team_id": participant["teamId"],
        "summoner_id": participant["summonerId"]
        })

    return participants


def get_label(match_data):

    for team in match_data['teams']:
        if team['teamId'] == 100:
            if team['win']:
                win = 1
            else:
                win = 0
    return win

def get_current_participant_info(match_data, mass_region, region, api_key, summoner_n):


    participants = []
    team_id = 100
    for participant in match_data['participants']:

        participants.append({
        "champion_id": participant["championId"],
        "summoner_name": get_summoner_name(participant["summonerId"], region, api_key),
        "team_id": participant["teamId"],
        "summoner_id": participant["summonerId"]
        })
        if participant["summonerName"] == summoner_n:
            team_id = participant["teamId"]

    return participants, team_id


def get_predict_data(summoner_name, mass_region, region, api_key, nof_stats, scp,
                    ratio_columns, tags_columns= None, nof_tags=0):

    summoner_id = get_summonerid(summoner_name, region, api_key)
    current_match = get_current_match(summoner_id, region, api_key)
    participants, team_id = get_current_participant_info(current_match, mass_region,
                                                region, api_key, summoner_name)
    data = scp.get_ratios(participants, nof_stats, ratio_columns, region, api_key)
    print(data)
    if tags_columns:
        allies, enemies = scp.get_tags(participants, nof_tags)
        data.extend(allies)
        data.extend(enemies)
        X = pd.DataFrame([data], columns=(ratio_columns + tags_columns))
    else:
        X = pd.DataFrame([data], columns=ratio_columns)
    return X, team_id


if __name__ == "__main__":
    api_key = "RGAPI-a384a673-d288-42ec-a860-55a1602dba94"
    summoner_name = 'Sứ Giả Lọk Khe'
    region = 'vn2'
    mass_region = "sea"
    no_games = 5
    queue_id = 450

    puuid = get_puuid(summoner_name, region, api_key)
    match_ids = get_match_ids(puuid, mass_region, no_games, queue_id, api_key)
    games, df = gather_data(puuid, match_ids, mass_region, api_key)
