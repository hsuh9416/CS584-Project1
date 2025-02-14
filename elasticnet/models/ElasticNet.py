# Algorithm to submit as Project1
import numpy as np


# 완성 예정본
class ElasticNetModel:
    def __init__(self, learning_rate: float, epochs: int, alpha: float, rho: float, optimization=False):
        self.ns = None  # Number of samples
        self.nf = None  # Number of features
        self.X = None  # Training Set - Parameters
        self.Y = None  # Training Set - Labels
        self.lr = learning_rate  # Learning rate
        self.epochs = epochs  # Number of Iteration
        self.l1_lambda = alpha * rho  # λ for L1(LASSO) : λ_1 = α*ρ
        self.l2_lambda = alpha * (1 - rho)  # λ for L2(RIDGE) : λ_2 = α*(1-ρ)
        self.w = None  # Init weights(parameters) of the model
        self.b = 0  # Init bias(parameter) of the model
        self.cost = -1  # Init cost function of the model
        self.optimization = optimization  # Whether to find optimal cost option
        self.models = []  # List to store train results
        self.epoch = epochs  # Best epoch for the best fit model

    def fit(self, x: np.ndarray, y: np.ndarray) -> object:
        """
        Train to build a predictive model
        :param x: input training data
        :param y: target training data
        :return: class ElasticNetModelResults object for prediction
        """
        # Preprocess the data
        self.ns, self.nf = x.shape  # Collect shape

        # Number conversion
        self.X = x.astype(np.float64) if not np.issubdtype(x.dtype, np.number) else x
        self.Y = y.astype(np.float64) if not np.issubdtype(y.dtype, np.number) else y
        if self.Y.shape == (self.Y.shape[0],):  # Fix '(n, )' shape
            self.Y = self.Y[:, np.newaxis]

        # Init parameters
        self.w = np.zeros((self.nf, 1))
        self.b = 0

        # Training
        for trial in range(self.epochs):
            self.cost = self.update_weights()
            self.models.append((trial + 1, self.w, self.b, self.cost))

        return ElasticNetModelResults(self)

    def cost_function(self, y, y_pred):
        """
        cost_function()
        This function computes the cost function of the given weights
        Formula used:
            C(β) = MSE + L1 + L2
                 = [(1/2N)*∑(y_i - y_pred_i)²] + [α * ρ * ∑|β_i|] + [(1/2) * α * (1-ρ) * ∑(β_i)²]
        where:
            N        : Number of samples
            y_i      : actual weight of ith feature
            y_pred_i : predicted weight of ith feature
            β_i      : weight of ith feature
            α        : alpha parameter
            ρ        : rho parameter, L1 ratio

        :param y: Original target value
        :param y_pred: predicted target value
        :return computed cost function
        """
        l1_penalty = self.l1_lambda * np.sum(np.abs(self.w))
        l2_penalty = self.l2_lambda * 0.5 * np.sum(self.w ** 2)
        return 1 / (2 * self.ns) * np.sum((y_pred - y) ** 2) + (l1_penalty + l2_penalty)

    def update_weights(self) -> float:
        """
        update_weights()
        This function updates weights according to gradient descent. In the case of L1 regulation,
        each weight must be reviewed to see if it satisfies the soft thresholding condition,
        so it is reflected for each weight.
        Formula used:
            * Weight(jth) update
            dC(β_j)/d(β_j) = MSE_β_j + L1_β_j + L2_β_j
                 = [(-1/N) * ∑(X_ij)*(y_i - y_pred_i)] + [α * ρ * sign(β_j)] + [α * (1 - ρ) * β_j]
            β = β - (learning_rate)*dβ

            * Bias update
            dC(β_0)/d(β_0) = MSE_β_0
                = (-1/N) * ∑(y_i - y_pred_i)
            β_0(bias) = β - (learning_rate)*dβ

            * Soft Thresholding(jth)
               - If the absolute value of the weight is greater than λ_1, adjust it by λ_1.
               - In other cases, the weight is set to 0.
                β_j = sign(β_j) * max(|β_j| - L1_β_j, 0)
                    = sign(β_j) * max(|β_j| - α * ρ, 0)
        where:
            N        : Number of samples
            y_i      : actual weight of ith feature
            y_pred_i : predicted weight of ith feature
            β_i      : weight of ith feature
            β_0      : constant, bias factor
            α        : alpha parameter
            ρ        : rho parameter, L1 ratio * λ_1 = α * ρ, λ_2 = α * (1-ρ)
            sign(β_j): Return 1 if jth feature is positive, -1 if jth feature is negative, otherwise returns 0

        :return: cost function of the current trial
        """
        # Here, self.weights acts like column vector as (n_features, ) for the computation purpose
        Y_pred = self.X.dot(self.w) + self.b
        residuals = self.Y - Y_pred
        dW = np.zeros((self.nf, 1))

        # should collect the derivation due to L1
        for j in range(self.nf):
            MSE = - np.dot(self.X[:, j], residuals) / self.ns
            L1 = self.l1_lambda * np.sign(self.w[j])  # L1 penalty
            L2 = self.l2_lambda * self.w[j]  # L2 penalty
            # Update the gradient with MSE, L1, and L2
            dW[j] = MSE + L1 + L2

        # get bias
        db = - np.sum(residuals) / self.ns

        # Apply weight&bias updates
        self.w = self.w - self.lr * dW
        self.b = self.b - self.lr * db

        # Apply soft thresholding after weight update
        for j in range(self.nf):
            self.w[j] = np.sign(self.w[j]) * np.maximum(np.abs(self.w[j]) - self.l1_lambda, 0)

        return self.cost_function(self.Y, Y_pred)


class ElasticNetModelResults:
    def __init__(self, model: ElasticNetModel):
        self.model = model  # trained model
        self.models = self.model.models
        self.w = self.model.w
        self.b = self.model.b
        self.epoch = self.model.epoch
        self.cost = self.model.cost
        if self.model.optimization:  # If apply optimization
            self.epoch, self.w, self.b, self.cost = min(self.models, key=lambda a: a[3])

    def predict(self, x: np.ndarray) -> np.ndarray:
        """
        Predict the output of the model with respect to the input data and return the predicted values
        :param x: Input data to test the model
        :return: Predicted values for the input data
        """
        x = x.astype(np.float64)  # Preprocessing the data
        return np.dot(x, self.model.w) + self.model.b
