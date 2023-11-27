# Description
## Aim
League of Legends (LOL) is an online competitive battle arena game. The game consists of two teams
with five players each. In the ARAM game mode, the map has only one lane and a team wins by
destroying the other team’s “Nexus”. ARAM game mode is skill based, relying less on the economy and
strategy aspect of the game, compared to the regular mode. As a result, a team’s strength is represented by
the combat skill of the players. This application focuses on predicting ARAM games outcomes using
supervised machine learning methods. The next part will discuss problem formulation and explain the
data points, features and labels used in this ML problem. The third part goes into details about the used
methods.

## Tools
Sklearn built-in decision tree and random forest classifier are utilized.<br>
The entire project is done in Python.
The dataset is generated from riotAPI and blitz.gg.<br>
## Files
The code for querying from Riot API is in the “riot.py” file.<br>
The code for web scraping is in “scraper.py” file. <br>
The data is then transformed, as stated in chapter 2.3 of the pdf report, and saved into a SQLite database.<br>
The report is in the file "Predict LOL ARAM games outcomes using Decision tree & Random forest classifier.pdf".<br>

# Conclusion <br>
This report applies decision tree classifier and random forest classifier to predict an ARAM
match outcome, using the teams’ players average strength metrics. The models are chosen to
account for non-linear relationships in the data. The features are chosen based on domain
knowledge. Given the results, it is clear that the game outcome can be predicted fairly
satisfactorily. However, the results are quite optimistic and leave room for improvement. Firstly,
the process of data collection (as mentioned in features and labels section) leads to the dataset
containing many matches from the same set of players. Nevertheless, a complete dataset
containing random matches from random players requires prolonged data collection, or special
permission from Riot Games. Moreover, the features selection and engineering process may
benefit from more sophisticated methods. For example, more related features could be used.
Dimensionality reduction methods, such as PCA, can be conducted with new features. Such data
would take more time to collect and clean. In conclusion, although the result is quite satisfactory,
a more complete dataset can greatly benefit the performance of predicting unseen data.
