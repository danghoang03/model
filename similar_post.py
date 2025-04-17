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
        SELECT title, description, subject
        FROM posts
        WHERE id = %s;
    """
    cursor.execute(query, (post_id,))
    post_result = cursor.fetchone()
    title, description, subject = post_result
    post_data = {"title": title, "description": description, "subject": subject}
    
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

def get_all_posts_by_subject(subject, post_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    query = """
        SELECT
            p.id,
            p.title,
            p.description,
            COALESCE(ARRAY_AGG(t.name ORDER BY t.name), ARRAY[]::varchar[]) AS tags
        FROM
            posts p
        LEFT JOIN
            post_has_tags pht ON p.id = pht.post_id
        LEFT JOIN
            tags t ON pht.tag_id = t.id
        WHERE
            p.subject = %s AND p.id != %s
        GROUP BY
            p.id, p.title, p.description  
        ORDER BY
            p.id; 
    """
    cursor.execute(query, (subject, post_id))
    results = cursor.fetchall()
    conn.close()
    return results

def compute_cosine_similarity(vec1, vec2):
    dist = cosine(vec1, vec2)  
    sim = 1 - dist            
    return sim
