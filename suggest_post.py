import os
import psycopg2
import select
import random
import numpy as np
from pickle import load
from scipy.spatial.distance import cosine
from gensim.models import LdaModel
from gensim.corpora.dictionary import Dictionary
from numpy import ravel
from itertools import combinations

MODELS_DIR = "models"
DATA_DIR = "data"
DB_CONFIG = {
    "dbname": "tc-sharing",
    "user": "postgres",
    "password": "123456",
    "host": "localhost",
    "port": "5432"
}

# Số lượng bài post được lấy để tính pp chủ đề cho sinh viên
N = 2
# Số lần lặp
ITERATIONS = 1000

def get_student_recent_running_posts(student_email, limit):
    """
    Lấy ra danh sách post_id mà sinh viên đã chạy (mới nhất) từ bảng studentRunTestcase.
    Chỉ lấy các post_id khác nhau và sắp xếp theo thời gian giảm dần.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    query = """
        SELECT DISTINCT post_id, time
        FROM studentRunTestcase
        WHERE student_mail = %s
        ORDER BY time DESC
        LIMIT %s;
    """
    cursor.execute(query, (student_email, limit))
    results = cursor.fetchall()
    conn.close()
    return [res[0] for res in results]

def load_post_topic_distribution(post_id):
    """
    Tải file pickle eval_post{post_id}.pkl và trả về phân phối chủ đề của post_id đó.
    Giả sử file pickle chứa một dict với key là post_id và value là dict có trường 'lda'.
    """
    filepath = os.path.join(DATA_DIR, f"eval_post_{post_id}.pkl")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'rb') as f:
        data = load(f)
    if post_id in data:
        return np.array(data[post_id]["lda"])
    
def compute_average_distribution(post_ids):
    """
    Tính trung bình phân phối chủ đề của danh sách post_ids.
    """
    distributions = []
    for pid in post_ids:
        try:
            lda_dist = load_post_topic_distribution(pid)
            distributions.append(lda_dist)
        except Exception as e:
            print(f"Error loading post {pid}: {e}")
    if not distributions:
        return None
    return np.mean(distributions, axis=0)

def load_subject_materials(subject):
    """
    Tải file eval_{subject}.pkl chứa kết quả tài liệu môn học.
    Giả sử file chứa dict với các key: "material_results" (mỗi phần tử có trường "lda")
    và "mapping" (mapping từ document id đến list [course, chapter, section]).
    """
    filepath = os.path.join(DATA_DIR, f"eval_{subject}.pkl")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Subject file not found: {filepath}")
    with open(filepath, 'rb') as f:
        data = load(f)
    return data

def determine_student_interest(base_distribution, subject_materials):
    """
    So sánh phân phối chủ đề của sinh viên với các tài liệu môn học.
    Trả về label (chapter) của tài liệu có khoảng cách cosine nhỏ nhất.
    """
    base_distribution = np.array(base_distribution, dtype=float).ravel()
    best_doc = None
    best_dist = float("inf")
    for doc_id, mat in subject_materials["material_results"].items():
        material_dist = np.array(mat["lda"], dtype=float).ravel()
        dist = cosine(base_distribution, material_dist)
        
        if dist < best_dist:
            best_dist = dist
            best_doc = doc_id
            
    course = "Unknown Course"
    chapter = "Unknown Chapter"

    for course_name, doc_ids in subject_materials["mapping"]["course"].items():
        if best_doc in doc_ids:
            course = course_name
            break

    for chapter_name, doc_ids in subject_materials["mapping"]["chapters"].items():
        if best_doc in doc_ids:
            chapter = chapter_name
            break

    trace_string = f"{course} > {chapter}"
    return trace_string

def get_candidate_posts(subject, interest_label, limit_hot, limit_new):
    """
    Lấy ra 20 bài post ứng với nội dung mà sinh viên quan tâm dựa trên trường trace,
    gồm 10 bài post có độ hot cao nhất (tổng số lượt tương tác + số comment)
    và 10 bài post mới nhất vừa được up lên.
    Trả về list các post_id.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    like_pattern = f"{interest_label}%"
    
    # Lấy N bài post hot nhất: tổng số lượt tương tác + số comment
    query = """
        SELECT p.id, (COALESCE(i.interaction_count, 0) + COALESCE(c.comment_count, 0)) as hot_score
        FROM posts p
        LEFT JOIN (
            SELECT post_id, COUNT(*) as interaction_count
            FROM interactions
            GROUP BY post_id
        ) i ON p.id = i.post_id
        LEFT JOIN (
            SELECT post_id, COUNT(*) as comment_count
            FROM comments
            GROUP BY post_id
        ) c ON p.id = c.post_id
        WHERE p.subject = %s AND p.trace LIKE %s
        ORDER BY hot_score DESC, p.created_at DESC
        LIMIT %s
    """
    cursor.execute(query, (subject, like_pattern, limit_hot))
    hot_results = cursor.fetchall()
    hot_posts = [r[0] for r in hot_results]
    
    # Lấy N bài post mới nhất dựa trên created_at
    query = """
        SELECT id
        FROM posts
        WHERE subject = %s AND trace LIKE %s
        ORDER BY created_at DESC
        LIMIT %s;
    """
    cursor.execute(query, (subject, like_pattern, limit_new))
    new_results = cursor.fetchall()
    new_posts = [r[0] for r in new_results]
    
    conn.close()
    
    candidate_posts = list(set(hot_posts + new_posts))
    return candidate_posts

def eval_best_suggest(candidate_posts, base_distribution, n):
    """
    Duyệt qua tất cả tổ hợp C(len(candidate_posts), n).
    Tìm tổ hợp có khoảng cách cosine nhỏ nhất với base_distribution.
    """
    base_distribution = np.array(base_distribution, dtype=float).ravel()
    best_suggest = None
    best_distance = float("inf")
    
    all_groups = combinations(candidate_posts, n)  # Tất cả tổ hợp chọn n từ candidate_posts
    
    for group in all_groups:
        group_avg = compute_average_distribution(group)
        group_avg = np.array(group_avg , dtype=float).ravel()
        dist = cosine(base_distribution, group_avg)
        if dist < best_distance:
            best_distance = dist
            best_suggest = group
    
    return best_suggest


def main():
    student_email = "son.nguyenthai@hcmut.edu.vn"
    recent_posts = get_student_recent_running_posts(student_email, N)
    if not recent_posts:
        print("No recent student run testcases found.")
        return
    print(f"Recent student run posts: {recent_posts}")
    
    # Tính phân phối chủ đề gốc của sinh viên
    base_distribution = compute_average_distribution(recent_posts)
    if base_distribution is None:
        print("Error computing base distribution.")
        return
    print(f"Student base topic distribution: {base_distribution}")
    
    subject = "DSA"
    subject_materials = load_subject_materials(subject)
    
    interest_label = determine_student_interest(base_distribution, subject_materials)
    if interest_label is None:
        print("Could not determine student interest from subject materials.")
        return
    print(f"Student appears to be interested in material: {interest_label}")
    
    candidate_posts = get_candidate_posts(subject, interest_label, 3, 3)
    if not candidate_posts:
        print("No candidate posts found matching the interest label.")
        return
    print(f"Candidate posts: {candidate_posts}")
    
    best_suggest = eval_best_suggest(candidate_posts, base_distribution, N)
    if best_suggest is None:
        print("No valid combination found.")
        return

    print(f"Suggest {N} posts: {best_suggest}")
    
if __name__ == "__main__":
    main()