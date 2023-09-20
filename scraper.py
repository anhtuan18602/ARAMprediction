from riot import *

import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup



class Scraper():
    __slots__ = ("champions_info", "champions_tags", "blitz_url", "all_tags","banned", "logr_url", "logr_region")

    def __init__(self, path: Path,file_name: str, tags, region) -> None:
        region_formatter = {
                            "oc1": "oce", "ph2": "ph", "sg2": "sg", "th2": "th", "tw2": "tw", "vn2": "vn",
                            "jp1": "jp", "kr": "kr",
                            "na1": "na", "br1": "br", "la1": "lan", "la2": "las",
                            "eun1": "eune", "euw1": "euw", "tr1": "tr", "ru": "ru"
                        }
        self.logr_region = region_formatter[region]
        self.blitz_url =  'https://blitz.gg/lol/profile/' + region + '/'
        self.logr_url =  'https://www.leagueofgraphs.com/summoner/champions/'
        with open((path / file_name).resolve(), "r", encoding='utf-8') as json_file:
            data_dict = json.load(json_file)
        champs_info = {}
        champs_tags = {}
        for champ in data_dict["data"].values():
            champs_info[int(champ["key"])] = champ["info"]
            champs_tags[int(champ["key"])] = champ["tags"]

        self.all_tags = tags
        self.champions_info = champs_info
        self.champions_tags = champs_tags
        self.banned = {}

    def blitz_scrape(self,summoner_name, champion_id=None):
        if champion_id:
            url = f"{self.blitz_url}{summoner_name}/champions/all/{champion_id}?queue=HOWLING_ABYSS_ARAM"
        else:
            url = f"{self.blitz_url}{summoner_name}/champions/all?queue=HOWLING_ABYSS_ARAM"
        response = requests.get(url)
        bs = BeautifulSoup(response.content, 'html.parser')

        stats = bs.find_all('section', {'class': '⚡a79e7daf span-quarter card-body'})
        try:
            nof_games = bs.find_all('span', {'class': 'type-body2'})[1]
        except:
            return [],0
        return stats, nof_games



    def get_tags_count(self,summoner_name, champion_id):
        tags_count = dict.fromkeys(self.all_tags, 0)
        for tag in self.champions_tags[champion_id]:
            tags_count[tag] += 1
        return list(tags_count.values())


    def scrape(self, summoner_name, champion_id, columns):


        scraped, nof_games_scraped = self.blitz_scrape(summoner_name, champion_id=champion_id)

        if len(scraped) == 0:
            scraped, nof_games_scraped = self.blitz_scrape(summoner_name)
        if len(scraped) == 0:
            print([0.5, 3.0, 800, 5])
            return [0.5, 3.0, 800, 5]

        features = []

        for column in columns:
            if column == "m_winrate":
                winrate_str = scraped[0].find('h3').get_text()
                winrate = float(winrate_str[:-1])/100
                features.append(winrate)
            if column == "m_kda":
                try:
                    kda_str = scraped[1].find('h3').get_text()
                    if kda_str == 'NaN':
                        return None
                    kda = float(kda_str)
                except:
                    kda = float(10)
                features.append(kda)
            if column== "m_dmg":
                dmg_str = scraped[3].find('h3').get_text()
                dmg = float(dmg_str.replace(',',''))
                features.append(dmg)
            if column== "m_nof_games":
                nof_games_str = nof_games_scraped.get_text()
                nof_games = int(nof_games_str.split()[0])
                features.append(nof_games)
        print(features)
        return features


    def get_ratios(self, participants, nof_ratios, columns, region, api_key):

        allies = [0] * nof_ratios
        enemies = [0] * nof_ratios
        print(allies)
        for participant in participants:
            mastery = get_mastery(participant['summoner_id'],
            participant['champion_id'], region, api_key)

            scraped_stats = self.scrape(
            participant['summoner_name'],
            participant['champion_id'],
            columns)
            if not scraped_stats:
                return None
            if not mastery:
                return None
            scraped_stats.append(mastery["championPoints"])

            if participant['team_id'] == 100:
                for j in range(nof_ratios):
                    allies[j] += scraped_stats[j]

            else:
                for j in range(nof_ratios):
                    enemies[j] += scraped_stats[j]

        ratio = [x - y for x, y in zip(allies, enemies)]
        print(ratio)
        return ratio


    def get_tags(self, participants, nof_tags):

        allies = [0] * nof_tags
        enemies = [0] * nof_tags

        for participant in participants:

            tags_count = self.get_tags_count(
            participant['summoner_name'],participant['champion_id'])
            if not tags_count:
                return None

            if participant['team_id'] == 100:
                for j in range(nof_tags):
                    allies[j] += tags_count[j]

            else:
                for j in range(nof_tags):
                    enemies[j] += tags_count[j]
        print(allies, enemies)
        return allies, enemies



    def gather_training(self, mass_region, region, api_key, nof_ratios, db,
    ratios_columns, tags_columns, nof_tags):

        match_ids = db.get_matches()

        for match_id in match_ids:
            print(match_id)
            match_data = get_match_data(match_id, mass_region, api_key)['info']
            participants = get_participants_info(match_data, region, api_key, scp)
            label = get_label(match_data)
            ratios = self.get_ratios(participants, nof_ratios, ratios_columns, region, api_key)
            allies, enemies = self.get_tags(participants, nof_tags)
            if not ratios:
                db.delete_match(match_id)
                print(f"Not enough game info. Deleted {match_id}.")
                continue

            db.add_training(match_id, ratios, label)
            db.add_tags(match_id, allies, enemies, nof_tags)



def init_scraper(region):
    path = Path(".")
    file_name = 'champion.json'
    tags = ['Mage', 'Marksman', 'Tank', 'Assassin', 'Support', 'Fighter']
    return Scraper(path, file_name, tags, region)

if __name__ == "__main__":
    champion_name = 'Draven'
    summoner_name = 'UnbeatableVN'

    stats = blitz_scrape(champion_id, summoner_name)
