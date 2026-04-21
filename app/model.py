import mlflow.pyfunc

model = None


def load(path: str):
    global model
    model = mlflow.pyfunc.load_model(path)
