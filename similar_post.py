import os
import psycopg2
from gensim.models import LdaModel
from gensim.corpora.dictionary import Dictionary
from gensim.parsing.preprocessing import preprocess_string
from scipy.spatial.distance import cosine

MODELS_DIR = "models"
DATA_DIR = "data"
DB_CONFIG = {
    "dbname": "tc-sharing",
    "user": "postgres",
    "password": "123456",
    "host": "localhost",
    "port": "5432"
}

def get_post_distribution(post, dictionary, lda_model):
    post_corpus = dictionary.doc2bow(post)
    chunk = (post_corpus, )
    lda_a_gamma = lda_model.inference(chunk=chunk)[0]
    return lda_a_gamma

def get_all_posts_by_subject(subject):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    query = """
        SELECT id, title, description
        FROM posts
        WHERE subject = %s;
    """
    cursor.execute(query, (subject,))
    results = cursor.fetchall()
    conn.close()
    # Mỗi phần tử results là (id, title, description)
    return results

def compute_cosine_similarity(vec1, vec2):
    dist = cosine(vec1, vec2)  
    sim = 1 - dist            
    return sim