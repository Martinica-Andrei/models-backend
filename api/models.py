from flask import Blueprint, g, jsonify
from .blueprint import api_blueprint
from db import db
from decorators.login_required import login_required
from lightfm import LightFM
import numpy as np
from load_book_recommendation_model import model
from scipy.sparse import csr_matrix
import joblib
import utils
from db_models.book import Book
import pandas as pd

models_blueprint = Blueprint('models', __name__,
                            url_prefix='/models')
api_blueprint.register_blueprint(models_blueprint)


def add_new_users(model : LightFM, user_id):

    nr_users = model.get_user_representations()[0].shape[0]
    nr_users_to_add = user_id - (nr_users - 1)
    if nr_users_to_add <= 0:
        return
    
    new_user_embedding_gradients = np.zeros((nr_users_to_add, model.no_components))
    new_user_embedding_momentum = np.zeros((nr_users_to_add, model.no_components))

    new_user_bias_gradients = np.zeros(nr_users_to_add)
    zeros_bias = np.zeros(nr_users_to_add)

    if model.learning_schedule == "adagrad":
        new_user_embedding_gradients += 1
        new_user_bias_gradients += 1

    model.user_embeddings = np.concatenate([model.user_embeddings, np.random.rand(nr_users_to_add, model.no_components)], axis=0, dtype=np.float32)
    model.user_embedding_gradients = np.concatenate([model.user_embedding_gradients, new_user_embedding_gradients], axis=0, dtype=np.float32)
    model.user_embedding_momentum = np.concatenate([model.user_embedding_momentum, new_user_embedding_momentum], axis=0, dtype=np.float32)
    model.user_biases = np.concatenate([model.user_biases, zeros_bias], axis=0, dtype=np.float32)
    model.user_bias_gradients = np.concatenate([model.user_bias_gradients, new_user_bias_gradients], axis=0, dtype=np.float32)
    model.user_bias_momentum = np.concatenate([model.user_bias_momentum, zeros_bias], axis=0, dtype=np.float32)

def is_user_added(model, user_id):
    nr_users = model.get_user_representations()[0].shape[0]
    return user_id < nr_users

    
@models_blueprint.post("/books/user_train")
@login_required
def books_train_on_user():
    if is_user_added(model, g.user.id) == False:
        add_new_users(model, g.user.id)
    positive_book_ratings = np.array([rating.book_id for rating in g.user.book_ratings if rating.rating == 'Like'])
    if len(positive_book_ratings) < 5:
        return {"err" : "Minimum 5 positive ratings are required for training!"}, 400
    ones = np.ones_like(positive_book_ratings)
    user_id_arr = np.full_like(ones, g.user.id)

    nr_books = model.get_item_representations()[0].shape[0]
    nr_users = model.get_user_representations()[0].shape[0]

    y = csr_matrix((ones, (user_id_arr, positive_book_ratings)), shape=(nr_users, nr_books), dtype=int)

    def train_model():
        epochs = 1000
        for i in range(1, epochs + 1):
            model.fit_partial(y, epochs=1, num_threads=8)
            yield f"{i / epochs}\n"
    joblib.dump(model, utils.BOOKS_DATA_MODEL)
    return train_model()

@models_blueprint.get("/books/user_recommendations")
@login_required
def books_recommendations():
    if is_user_added(model, g.user.id) == False:
        return {"err" : "First train model!"}, 400
    books_not_to_show = np.array([rating.book_id for rating in g.user.book_ratings])

    nr_books = model.get_item_representations()[0].shape[0]
    books_indices = np.arange(nr_books)

    predictions = model.predict(g.user.id, books_indices)
    prediction_indices_sorted = np.argsort(-predictions)
    prediction_indices_sorted = prediction_indices_sorted[np.isin(prediction_indices_sorted, books_not_to_show) == False]

    p = prediction_indices_sorted[:100].tolist()

    books = db.session.query(Book).filter(Book.id.in_(p))
    books = [{'id' : book.id, 'title' : book.title} for book in books]

    df = pd.DataFrame(books)
    df.set_index('id', inplace=True)
    df = df.reindex(index=p)
    df.reset_index(inplace=True)

    return df.to_json(orient='records')