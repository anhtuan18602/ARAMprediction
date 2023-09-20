from riot import *
from db import *
from scraper import *
from model import *

class Predictor():
    __slots__ = ("ratio_columns", "tags_columns", "nof_tags", "nof_ratios",
                "mass_region", "region", "api_key", "db", "scp", "model")

    def __init__(self, region, api_key):
        region_to_mass = {
                            "oc1": "sea", "ph2": "sea", "sg2": "sea", "th2": "sea", "tw2": "sea", "vn2": "sea",
                            "jp1": "asia", "kr": "asia",
                            "na1": "americas", "br1": "americas", "la1": "americas", "la2": "americas",
                            "eun1": "europe", "euw1": "europe", "tr1": "europe", "ru": "europe"
                        }
        self.ratio_columns = ['m_winrate', 'm_kda', 'm_dmg', 'm_nof_games','m_mastery']
        self.tags_columns   =  ['a_mage', 'a_marksman', 'a_tank', 'a_assassin', 'a_support', 'a_fighter',
                                'e_mage', 'e_marksman', 'e_tank', 'e_assassin',  'e_support', 'e_fighter']
        self.nof_tags = int(len(self.tags_columns)/2)
        self.nof_ratios = len(self.ratio_columns)
        self.region = region
        self.mass_region =  region_to_mass[region]
        self.api_key = api_key
        self.db = init_database()
        self.scp = init_scraper(region)
        self.model = Model()

    def gather(self):
        scp.gather_training(self.mass_region, self.region, self.api_key, self.nof_ratios,
                    self.db, self.ratios_columns, self.tags_columns, self.nof_tags)


    def train(self):
        data = self.db.get_model_data(self.ratio_columns, self.tags_columns)
        features = data[(self.ratio_columns+self.tags_columns)]
        target = data["target"]
        self.model.train_model(features, target)


    def print_results(self, team_id, proba, prediction):
        print(team_id, prediction)
        prediction_value = prediction[0]
        first_team_lose = proba[0][0]
        first_team_win = proba[0][1]

        if team_id == 100:
            print(f"your team ---{first_team_win*100}% - {first_team_lose*100}%--- enemy team")
        else:
            print(f"your team ---{first_team_lose*100}% - {first_team_win*100}%--- enemy team")

    def test_predict(self):
        team_id = 200
        data = [1.23,	2.71,	-84.9,	-55,	-673974,	1,	2,	2,
        2,	1,	1,	3,	2,	1,	0,	1,	1]

        X = pd.DataFrame([data], columns=(self.ratio_columns + self.tags_columns))

        proba, prediction = self.model.predict(X)
        self.print_results(team_id, proba, prediction)

    def predict(self, summoner_name):

        X, team_id = get_predict_data(summoner_name, self.mass_region, self.region,
                            self.api_key, self.nof_ratios, self.scp,
                            self.ratio_columns, tags_columns= self.tags_columns,
                            nof_tags=self.nof_tags)
        print(X)
        proba, prediction = self.model.predict(X)
        self.print_results(team_id, proba, prediction)


if __name__ == "__main__":

    ratio_columns = ['m_winrate', 'm_mastery']#['m_winrate', 'm_kda', 'm_dmg', 'm_nof_games','m_mastery']
    tags_columns   =  ['a_mage', 'a_marksman', 'a_tank', 'a_assassin', 'a_support', 'a_fighter',
                         'e_mage', 'e_marksman', 'e_tank', 'e_assassin',  'e_support', 'e_fighter']
    nof_tags = 6
    nof_ratios = len(ratio_columns)

    summoner_name = "Cozy Bearrrrr"

    region = 'vn2'
    mass_region = 'sea'
    api_key = "RGAPI-a384a673-d288-42ec-a860-55a1602dba94"
    #win_prob = get_win_probability(summoner_name, region, api_key)
    """
    db = init_database()
    scp = init_scraper(region)
    #
    data = db.get_model_data(ratio_columns, tags_columns)
    #
    model = Model(data[(ratio_columns+ tags_columns)], data["target"], scp)
    model.save_model()
    #model.predict(X)
    """
    predictor = Predictor(region, api_key)
    predictor.train()
    #predictor.predict(summoner_name)
