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

def get_post_information(post_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    query = """
        SELECT title, description 
        FROM posts
        WHERE id = %s;
    """
    cursor.execute(query, (post_id,))
    post_result = cursor.fetchone()
    title, description = post_result
    post_data = {"title": title, "description": description}
    
    query = """
        SELECT T.name
        FROM tags T
        INNER JOIN post_has_tags P ON T.id = P.tag_id
        WHERE P.post_id = %s;
    """
    cursor.execute(query, (post_id,))
    tag_results = cursor.fetchall()
    conn.close()
    tag_names = [row[0] for row in tag_results]
    post_data["tags"] = tag_names
    return post_data
    
    return results
    

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