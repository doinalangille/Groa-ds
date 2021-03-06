import gensim
import numpy as np
import pandas as pd
import psycopg2
import re
import os


def prep_reviews(df):
    """Converts Letterboxd reviews dataframe to list of concatenated reviews."""
    reviews = df['Review'].tolist()
    for i in reviews:
        i = i.lower()
    return reviews

class r2v_Recommender():
    def __init__(self, model_path, cursor_dog):
        """Initialize model with name of .model file"""
        self.model_path = model_path
        self.model = None
        self.cursor_dog = cursor_dog

    def _get_model(self):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if self.model == None:
            model_path = self.model_path
            d2v_model = gensim.models.Doc2Vec.load(model_path)
            # Keep only the normalized vectors.
            # This saves memory but makes the model untrainable (read-only).
            d2v_model.init_sims(replace=True)
            self.model = d2v_model
        return self.model

    def predict(self, reviews, hist_list=[], n=50, max_votes=50000):
        """Returns a list of recommendations and useful metadata, given a pretrained
        word2vec model and a list of movies.

        Parameters
        ----------

            reviews: string
                string of concatenated user reviews.

            hist_list : iterable
                list of movies the user has seen.

            n : int
                number of recommendations to return.

            max_votes : int
                maximum number of votes for a movie to be considered a hidden gem.

        Returns
        -------
        Two lists of tuples: hidden_gems and cult_movies
        (Title, Year, URL, # Votes, Avg. Rating, User Rating, Reviewer, Review, Movie ID)
        """

        clf = self._get_model()

#         def _remove_dupes(recs, good_movies, bad_movies):
#             """remove any recommended IDs that were in the good_movies list"""
#             all_rated = good_movies + bad_movies
#             if hist_list:
#                 all_rated = list(set(all_rated+hist_list))
#             dupes = [x for x in recs if x[0] in all_rated]
#             return [x for x in recs if x[0] not in all_rated]

        def similar_users(reviews, n_sims=30):
            """Get similar users based on reviews."""
            vec = clf.infer_vector(reviews)
            sims = clf.docvecs.most_similar([vec], topn=n_sims)
            return [x[0] for x in sims]

        def hidden_gems(sims, max_votes=50000, n=50):
            """Finds hidden gems (highly rated but unpopular).

            Parameters
            ----------
                sims : list
                    list of similar users.

                max_votes : int
                    max number of votes (ratings) for movies to be included.

                n : int
                    max number of results.

            Returns
            -------
            List of recommendations as tuples:
            (Title, Year, URL, # Votes, Avg. Rating, User Rating, Reviewer, Review)
            """
            simset = tuple(sims)
            hidden_query = f"""
                            SELECT  m.primary_title, m.start_year, m.movie_id mid,
                                    ra.num_votes num, ra.average_rating avgr,
                                    r.user_rating taste, r.user_name,
                                    r.review_text txt
                            FROM imdb_reviews r
                            JOIN imdb_movies m ON r.movie_id = m.movie_id
                            JOIN imdb_ratings ra ON r.movie_id = ra.movie_id
                            WHERE user_name IN {simset}
                            AND user_rating BETWEEN 8 AND 10
								AND ra.average_rating BETWEEN 7 AND 10
								AND ra.num_votes BETWEEN 1000 AND {max_votes}
                            ORDER BY ra.average_rating DESC
                            LIMIT {n}
                            """
            self.cursor_dog.execute(hidden_query)
            try:
                hidden_recs = self.cursor_dog.fetchall()
                hidden_recs = [list(x) for x in hidden_recs]
                for i in hidden_recs:
                    i.append(i[2]) # add ID to the end
                    i[2] = f"https://www.imdb.com/title/tt{i[2]}/" # add URL
                hidden_recs = [tuple(x) for x in hidden_recs]
            except Exception as e:
                print(e)
                hidden_recs = [("No hidden gems found! Better luck next time.",
                                None, None, None, None, None, None, None, None)]
            return hidden_recs

        def cult_movies(sims, n=50):
            """Takes a list of similar users to get cult movies (considered
                underrated by similar users).

            Parameters
            ----------
                sims : list
                    list of similar users.

                n : int
                    max number of results.

            Returns
            -------
            List of recommendations as tuples:
            (Title, Year, URL, # Votes, Avg. Rating, User Rating, Reviewer, Review)
            """
            simset = tuple(sims)
            cult_query = f"""
                            SELECT  m.primary_title, m.start_year, m.movie_id mid,
                                    ra.num_votes num, ra.average_rating avgr,
                                    r.user_rating taste, r.user_name,
                                    r.review_text txt
                            FROM imdb_reviews r
                            JOIN imdb_movies m ON r.movie_id = m.movie_id
                            JOIN imdb_ratings ra ON r.movie_id = ra.movie_id
                            WHERE user_name IN {simset}
                            AND user_rating BETWEEN 7 AND 10
								AND user_rating BETWEEN 6 AND 10
								AND user_rating >= (ra.average_rating + 3)
                            ORDER BY user_rating DESC
                            LIMIT {n}
                """
            self.cursor_dog.execute(cult_query)
            try:
                cult_recs = self.cursor_dog.fetchall()
                cult_recs = [list(x) for x in cult_recs]
                for i in cult_recs:
                    i.append(i[2]) # add ID to the end
                    i[2] = f"https://www.imdb.com/title/tt{i[2]}/" # add URL
                cult_recs = [tuple(x) for x in cult_recs]
            except Exception as e:
                print(e)
                cult_recs = [("No cult movies found! Better luck next time.",
                                None, None, None, None, None, None, None, None)]
            return cult_recs

        sims = similar_users(reviews, n_sims=30)
        cult_recs = cult_movies(sims, n=n/2)
        hidden_gems = hidden_gems(sims, n=n/2)
        return [cult_recs, hidden_gems]