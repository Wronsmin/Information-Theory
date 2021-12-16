import numpy as np 
import matplotlib.pyplot as plt 
import seaborn as sns 
from statsmodels.nonparametric.kernel_density import KDEMultivariate, KDEMultivariateConditional
import pandas as pd


class Classifier():
    def accuracy(self, y_test, y_pred):
        return np.sum(y_test == y_pred) / len(y_test)

    def visualize(self, y_true, y_pred, target):
        
        tr = pd.DataFrame(data=y_true, columns=[target])
        pr = pd.DataFrame(data=y_pred, columns=[target])
        
        
        fig, ax = plt.subplots(1, 2, sharex='col', sharey='row', figsize=(15,6))
        
        sns.countplot(x=target, data=tr, ax=ax[0], palette='viridis', alpha=0.7, hue=target, dodge=False)
        sns.countplot(x=target, data=pr, ax=ax[1], palette='viridis', alpha=0.7, hue=target, dodge=False)
        

        fig.suptitle('True vs Predicted Comparison', fontsize=20)

        ax[0].tick_params(labelsize=12)
        ax[1].tick_params(labelsize=12)
        ax[0].set_title("True values", fontsize=18)
        ax[1].set_title("Predicted values", fontsize=18)
        plt.show()


class Bayes_Classifier(Classifier):
    def fit(self, features, target, dep_type, indep_type, bw=None) -> None:
        self.n_classes = np.unique(target).size
        self.n_features = features.shape[1]

        self.Prior = np.unique(target, return_counts=True)[1] / target.size

        if bw == None:
            bw = 'normal_reference'
        else:
            bw = bw
        
        self.kde_Xc = KDEMultivariateConditional(endog=features, exog=target,
                                        dep_type=dep_type, indep_type=indep_type,
                                        bw=bw).pdf
        self.kde_X = KDEMultivariate(data=features, var_type=dep_type).pdf

    def evaluate(self, features):
        n = features.shape[0]

        PXc = np.array([self.kde_Xc(features, [i] * n) for i in range(self.n_classes)])
        PcX = ((PXc.T * self.Prior).T / self.kde_X(features)).T

        return np.argmax(PcX, axis=1)


class NB_classifier(Classifier):
    def fit(self, features, target, dep_type, indep_type, bw=None) -> None:
        self.n_classes = np.unique(target).size
        self.n_features = features.shape[1]

        self.Prior = np.unique(target, return_counts=True)[1] / target.size

        if bw == None:
            bw = 'normal_reference'
        else:
            bw = bw

        self.kde_Xc = []

        for i in range(self.n_features):
            self.kde_Xc.append(KDEMultivariateConditional(endog=features[:, i], exog=target, 
                                                     dep_type=dep_type, 
                                                     indep_type=indep_type, 
                                                     bw='normal_reference').pdf)
        
        self.kde_X = KDEMultivariate(features, var_type='cccc').pdf

        self.Prior = np.unique(target, return_counts=True)[1] / target.size
    
    def evaluate(self, features):
        n_rows = features.shape[0]
        c = np.zeros((n_rows, self.n_classes))
        
        for d in range(n_rows):
            for i in range(self.n_classes):
                tmp = 1
                for j in range(self.n_features):
                    tmp *= self.kde_Xc[j]([features[d, j]], [i])
                
                c[d, i] = tmp * self.Prior[i] / self.kde_X(features[d, :])
        return np.argmax(c, axis=1)
    

class Gaussian_NB(Classifier):
    def calc_statistics(self, features, target):
        self.mean = np.zeros((self.n_classes, self.n_features))
        self.var = np.zeros((self.n_classes, self.n_features))
        for c in self.classes:
            self.mean[c] = np.mean(features[target == c], axis=0)
            self.var[c] = np.var(features[target == c], axis=0)
        
        return self.mean, self.var

    def gaussian_density(self, features, class_idx):

        mean = self.mean[class_idx]
        var = self.var[class_idx]
        
        numerator = np.exp((-1/2)*((features - mean)**2) / (2 * var))
        denominator = np.sqrt(2 * np.pi * var)

        return numerator / denominator
    
    def calc_posterior(self, x):
        posteriors = np.zeros((self.n_rows, self.n_classes))

        for c in range(self.n_classes):
            prior = np.log(self.prior[c])
            conditional = np.sum(np.log(self.gaussian_density(x, c)), axis=1)
            posteriors[:, c] = prior + conditional
        
        return np.argmax(posteriors, axis=1)
    

    def fit(self, features, target):
        self.classes = np.unique(target)
        self.n_classes = len(self.classes)
        self.n_features = features.shape[1]
        self.n_rows = features.shape[0]

        self.prior = np.unique(target, return_counts=True)[1] / target.size
        self.calc_statistics(features, target)
    

    def predict(self, features):
        return self.calc_posterior(features)