import os
import psycopg2
from gensim.models import LdaModel
from gensim.corpora.dictionary import Dictionary
from gensim.parsing.preprocessing import preprocess_string
from scipy.spatial.distance import cosine
from pickle import load, dump
import numpy as np
from numpy import ravel

MODELS_DIR = "models"
DATA_DIR = "data"
DB_CONFIG = {
    "dbname": "tc-sharing",
    "user": "postgres",
    "password": "123456",
    "host": "localhost",
    "port": "5432"
}

def get_post_from_db(post_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    query = """
        SELECT subject, title, description FROM posts WHERE id = %s;
    """
    cursor.execute(query, (post_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0], {post_id: preprocess_string(result[1]) + preprocess_string(result[2])}
    return None, {}

# def process_post(json_file):
#     with open(json_file, 'r', encoding='utf-8') as f:
#         data = json.load(f)
    
#     preprocessed_post = {}
#     course_name = data['course_name']
#     post_id = data['post_id']
#     title = data['title']
#     content = data['content']
    
#     cleaned_title = preprocess_string(title)
#     cleaned_content = preprocess_string(content)
#     preprocessed_post[post_id] = cleaned_title + cleaned_content
    
#     return course_name, preprocessed_post

def eval_post(post, course_dictionary, lda_model):
    post_result = {}
    for post_id, post_content in post.items():
        post_corpus = course_dictionary.doc2bow(post_content)
        chunk = (post_corpus, )
        lda_a_gamma = lda_model.inference(chunk=chunk)[0]
        
        post_result[post_id] = {
            "lda": lda_a_gamma,
            "all_words": post_content,
            "unutilized_words": [w for w in post_content if w not in course_dictionary.token2id]
        }
    
    return post_result

def invert_mapping(mapping):
    """document to hierarchy labels.
    [course, chapters, sections]
    """
    inverted_mapping = {}
    for item_type, value_dict in mapping.items():
        # item_type one of [course, chapters, sections]
        for item_name, doc_ids in value_dict.items():
            for doc_id in doc_ids:
                doc_type = inverted_mapping.get(doc_id, [None, None, None])
                if item_type == "sections":
                    doc_type[2] = item_name
                elif item_type == "chapters":
                    doc_type[1] = item_name
                elif item_type == "course":
                    doc_type[0] = item_name
                else:
                    raise NotImplementedError(item_type)
                inverted_mapping[doc_id] = doc_type
    return inverted_mapping

def generate_topic_map(distance_options, material_results, lda):
    distance_function, sort_reverse = distance_options
    topic_map = {
         "lda_rank": []
    }
    
    for doc_id, material_result in material_results.items():
        m_lda = ravel(material_result["lda"])
        topic_map["lda_rank"].append((
            doc_id,
            distance_function(lda, m_lda)
        ))

    topic_map["lda_rank"].sort(
        key=lambda tup: tup[1], reverse=sort_reverse)
    return topic_map
    
def tracing_post(post_result, course_results):
    docid_to_labels = invert_mapping(course_results["mapping"])
    material_results = course_results["material_results"]
    post_topic_mapping = {}
    
    distance_functions = {
        "cosine": (cosine, False),  # function, reverse
        # "euclidean": (euclidean, False)
    }
    
    for key in distance_functions.keys():
        post_topic_mapping[key] = {}
    
    for post_id, post_result in post_result.items():
        all_words = post_result["all_words"]
        unutilized_words = post_result["unutilized_words"]
        lda = ravel(post_result["lda"])
        
        for dist_func_name, distance_options in distance_functions.items():
            post_topic_map = generate_topic_map(distance_options, material_results, lda)
            post_topic_mapping[dist_func_name][post_id] = post_topic_map
        
    return post_topic_mapping

def print_LDA_suggest(post_topic_mapping, course_results):
    docid_to_labels = invert_mapping(course_results["mapping"])
    top_mapping = {}
    for dist_func, post_mappings in post_topic_mapping.items():
        for post_id, topic_map in post_mappings.items():
            if topic_map["lda_rank"]:
                top_doc_id, top_similarity = topic_map["lda_rank"][0]
                if top_doc_id in docid_to_labels:
                    hierarchy = docid_to_labels[top_doc_id]
                    top_mapping[post_id] = {
                        "similarity": top_similarity,
                        "hierarchy": hierarchy
                    }   
    for post_id, info in top_mapping.items():
        hierarchy = info["hierarchy"]
        similarity = info["similarity"]
        if hierarchy:
            course, chapter, section = hierarchy
            trace = f"{course or 'Unknown Course'} > {chapter or 'Unknown Chapter'} > {section or 'Unknown Section'}"
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            query = """
                UPDATE posts SET trace = %s WHERE ID = %s;
            """
            cursor.execute(query, (trace, post_id))
            conn.commit()
            cursor.close()
            conn.close()
            print(
                f"{course or 'Unknown Course'} > "
                f"{chapter or 'Unknown Chapter'} > "
                f"{section or 'Unknown Section'} (Similarity: {similarity:.4f})"
            )
        else:
            print(f"LDA suggested: Unknown mapping for post_id {post_id} (Cosine Distance: {similarity:.4f})") 
            
def update_trace(post_id, trace_str):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    query = """
        UPDATE posts SET trace = %s WHERE ID = %s;
    """
    cursor.execute(query, (trace, post_id))
    conn.commit()
    cursor.close()
    conn.close()

# for i in range(1, 24):
#     post_id = i
#     course_name, preprocessed_post = get_post_from_db(post_id)

#     # print(course_name)
#     # print(preprocessed_post)

#     lda_model_path = os.path.join(MODELS_DIR, f"{course_name}_lda.model")
#     dictionary_path = os.path.join(MODELS_DIR, f"{course_name}_dictionary.dict")    
#     lda_model = LdaModel.load(lda_model_path)
#     dictionary = Dictionary.load(dictionary_path)

#     material_file_path = os.path.join(DATA_DIR, f"eval_{course_name}.pkl")
#     with open(material_file_path, 'rb') as f:
#         course_results = load(f)
    
#     post_result = eval_post(preprocessed_post, dictionary, lda_model)
#     # print(post_result)

#     output_eval_file = os.path.join(DATA_DIR, f"eval_post_{post_id}.pkl")
#     with open(output_eval_file, 'wb') as f:
#         dump(post_result, f)
    
#     post_topic_mapping = tracing_post(post_result, course_results)
#     # print(post_topic_mapping)
#     print_LDA_suggest(post_topic_mapping, course_results)
