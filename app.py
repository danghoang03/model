from flask import Flask, request, jsonify
import os
import traceback
import numpy as np
from pickle import load
from gensim.parsing.preprocessing import preprocess_string
from gensim.models import LdaModel
from gensim.corpora.dictionary import Dictionary
from numpy import ravel
from suggest_post import (
    get_student_recent_running_posts,
    compute_average_distribution,
    load_subject_materials,
    determine_student_interest,
    get_candidate_posts,
    eval_best_suggest,
    N  
)
from tracing_post import (
    get_post_from_db,
    eval_post,
    tracing_post,
    invert_mapping,
    update_trace
)

from similar_post import (
    get_all_posts_by_subject,
    get_post_distribution,
    compute_cosine_similarity
)

MODELS_DIR = "models"
DATA_DIR = "data"

app = Flask(__name__)

@app.route('/suggest', methods=['POST'])
def suggest():
    try:
        data = request.get_json()
        student_email = data.get("student_email")
        subject = "DSA"

        if not student_email:
            return jsonify({"error": "Thiếu student_email"}), 400

        recent_posts = get_student_recent_running_posts(student_email, N)
        if not recent_posts:
            return jsonify({"error": "Không tìm thấy bài post mà sinh viên đã chạy gần đây"}), 404

        base_distribution = compute_average_distribution(recent_posts)
        if base_distribution is None:
            return jsonify({"error": "Lỗi tính toán phân phối chủ đề gốc"}), 500

        subject_materials = load_subject_materials(subject)
        interest_label = determine_student_interest(base_distribution, subject_materials)
        if not interest_label:
            return jsonify({"error": "Không xác định được nội dung mà sinh viên quan tâm"}), 500

        candidate_posts = get_candidate_posts(subject, interest_label, 3, 3)
        if not candidate_posts:
            return jsonify({"error": "Không tìm thấy bài post ứng viên"}), 404

        best_suggest = eval_best_suggest(candidate_posts, base_distribution, N)
        if not best_suggest:
            return jsonify({"error": "Không tìm thấy gợi ý phù hợp"}), 404

        return jsonify({
            "suggested_posts": list(best_suggest),
            "interest_label": interest_label
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@app.route('/trace', methods=['POST'])
def trace():
    try:
        data = request.get_json()
        post_id = data.get("post_id")
        if not post_id:
            return jsonify({"error": "Thiếu post_id"}), 400

        course_name, preprocessed_post = get_post_from_db(post_id)
        if course_name is None:
            return jsonify({"error": f"Không tìm thấy bài post với post_id {post_id}"}), 404

        lda_model_path = os.path.join(MODELS_DIR, f"{course_name}_lda.model")
        dictionary_path = os.path.join(MODELS_DIR, f"{course_name}_dictionary.dict")
        lda_model = LdaModel.load(lda_model_path)
        dictionary = Dictionary.load(dictionary_path)

        material_file_path = os.path.join(DATA_DIR, f"eval_{course_name}.pkl")
        with open(material_file_path, 'rb') as f:
            course_results = load(f)

        post_result = eval_post(preprocessed_post, dictionary, lda_model)
        post_topic_mapping = tracing_post(post_result, course_results)
        docid_to_labels = invert_mapping(course_results["mapping"])
        trace_str = None
        for dist_func, post_mappings in post_topic_mapping.items():
            for p_id, topic_map in post_mappings.items():
                if topic_map["lda_rank"]:
                    top_doc_id, top_similarity = topic_map["lda_rank"][0]
                    if top_doc_id in docid_to_labels:
                        hierarchy = docid_to_labels[top_doc_id]
                        course, chapter, section = hierarchy
                        trace_str = f"{course or 'Unknown Course'} > {chapter or 'Unknown Chapter'} > {section or 'Unknown Section'}"
                        break
            if trace_str:
                break

        if not trace_str:
            return jsonify({"error": "Không xác định được liên kết cho bài post"}), 500
        
        update_trace(post_id, trace_str)
        
        return jsonify({
            "post_id": post_id,
            "trace": trace_str
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@app.route('/similar_post', methods=['POST'])
def similar_post():
    try:
        data = request.get_json()
        title = data.get("title")
        description = data.get("description")
        subject = "DSA"
        
        if not title or not description:
            return jsonify({"error": "Thiếu tiêu đề hoặc mô tả"}), 400
        
        lda_model_path = os.path.join(MODELS_DIR, f"{subject}_lda.model")
        dictionary_path = os.path.join(MODELS_DIR, f"{subject}_dictionary.dict")
        lda_model = LdaModel.load(lda_model_path)
        dictionary = Dictionary.load(dictionary_path)
        
        preprocessed_post = preprocess_string(title) + preprocess_string(description)
        new_post_dist = get_post_distribution(preprocessed_post, dictionary, lda_model)
        
        all_posts = get_all_posts_by_subject(subject)

        similar_posts = []
        for post_id, title, description in all_posts:
            # Preprocess bài post cũ
            preprocessed_post = preprocess_string(title) + preprocess_string(description)
            post_dist = get_post_distribution(preprocessed_post, dictionary, lda_model)

            # Tính độ tương tự
            sim = compute_cosine_similarity(np.array(new_post_dist).ravel(), np.array(post_dist).ravel())
            if sim >= 0.8:
                similar_posts.append({
                    "post_id": post_id,
                    "title": title,
                    "similarity": round(float(sim), 3)
                })
                
        similar_posts.sort(key=lambda x: x["similarity"], reverse=True)
        return jsonify({
            "similar_posts": similar_posts
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Chạy Flask server tại cổng 5000
    app.run(host="0.0.0.0", port=5000, debug=True)