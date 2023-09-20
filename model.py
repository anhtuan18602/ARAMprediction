from riot import *
from scraper import *

import joblib
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.inspection import permutation_importance
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import confusion_matrix
from sklearn.feature_selection import RFE, SelectKBest, f_classif

class Model():

    slots = ("features", "target", "model", "scaler")
    def __init__(self, features=None, target=None):
        if features:
            self.features = features
            self.target = target
            self.train_model(features, target)
        else:
            self.load_model()

    def correlation_matrix(self):
        correlation_matrix = self.features.corr()
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
        plt.title("Correlation Matrix")
        plt.show()


    def vif(features, columns):

        vif = pd.DataFrame()
        vif["Features"] = self.features.columns
        vif["VIF"] = [variance_inflation_factor(self.features.values, i)
                                    for i in range(self.features.shape[1])]
        print(vif)


    def stats_significance(self):
        X_with_intercept = sm.add_constant(self.features)
        model = sm.Logit(self.target, X_with_intercept)
        result = model.fit()
        # Get the summary of the model, which includes the t-values and p-values of the coefficients
        print(result.summary())


    def train_model(self, features, target):
        X = features
        y = target
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=34)

        #sns.pairplot(features[['m_winrate', 'm_kda', 'm_dmg', 'm_nof_games','m_mastery','target']], hue='target', palette={1: 'red', 0: 'blue'}, markers=["o", "s"], hue_order=[1, 0])
        #plt.show()

        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
        X_train = pd.DataFrame(X_train, columns=X.columns)
        X_test = pd.DataFrame(X_test, columns=X.columns)

        rf_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        rf_classifier.fit(X_train, y_train)

        y_pred = rf_classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        conf_matrix = confusion_matrix(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred)
        print("Accuracy:", accuracy)
        print("Precision:", precision)
        print("Recall:", recall)
        print("F1 Score:", f1)
        print("ROC AUC Score:", roc_auc)
        print("Confusion Matrix:\n", conf_matrix)
        print("\n")
        self.model = rf_classifier
        self.scaler = scaler
        self.save_model()

    def save_model(self):
        path = Path(".")
        model_file = 'league_model.joblib'
        scaler_file = 'league_scaler.pkl'
        joblib.dump(self.model, (path / model_file).resolve())
        joblib.dump(self.scaler, (path / scaler_file).resolve())

    def load_model(self):
        path = Path(".")
        model_file = 'league_model.joblib'
        scaler_file = 'league_scaler.pkl'
        self.model = joblib.load((path / model_file).resolve())
        self.scaler = joblib.load((path / scaler_file).resolve())


    def predict(self, X):

        scaled_data = self.scaler.transform(X)
        scaled_data_df = pd.DataFrame(scaled_data, columns=X.columns)
        return self.model.predict_proba(scaled_data_df), self.model.predict(scaled_data_df)
