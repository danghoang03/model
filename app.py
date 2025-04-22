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
    get_post_information,
    get_all_posts_by_subject,
    get_post_distribution,
    compute_cosine_similarity
)

from translate import(
    translate_and_update_post
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

        # Danh sách N bài post mà sinh viên chạy thử gần đây nhất kèm trọng số
        weighted_posts = get_student_recent_running_posts(student_email, N)
        if not weighted_posts:
            return jsonify({"error": "Không tìm thấy bài post mà sinh viên đã chạy gần đây"}), 404
        
        if len(weighted_posts) < N:
            error_message = f"Sinh viên phải chạy thử ít nhất {N} bài post để nhận được gợi ý"
            return jsonify({"error": error_message}), 400

        # Tính phân phối chủ đề gốc của sinh viên dựa trên trọng số
        base_distribution = compute_average_distribution(weighted_posts)
        if base_distribution is None:
            return jsonify({"error": "Lỗi tính toán phân phối chủ đề gốc"}), 500

        # Lấy phân phối chủ đề của tài liệu môn học
        subject_materials = load_subject_materials(subject)
        
        # Tìm phần nội dung mà sinh viên đang quan tâm
        interest_label = determine_student_interest(base_distribution, subject_materials)
        if not interest_label:
            return jsonify({"error": "Không xác định được nội dung mà sinh viên quan tâm"}), 500

        # Lấy ra danh sách các bài post phù hợp với nội dung mà sinh viên quan tâm
        candidate_posts = get_candidate_posts(subject, interest_label, 3, 3, weighted_posts)
        if not candidate_posts:
            return jsonify({"error": "Không tìm thấy bài post ứng viên"}), 404

        # Gợi ý N bài post phù hợp nhất
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

        # Load bài post có ID tương ứng từ DB
        subject, preprocessed_post = get_post_from_db(post_id)
        if subject is None:
            return jsonify({"error": f"Không tìm thấy bài post với post_id {post_id}"}), 404

        # Load model LDA + từ điển môn học tương ứng
        lda_model_path = os.path.join(MODELS_DIR, f"{subject}_lda.model")
        dictionary_path = os.path.join(MODELS_DIR, f"{subject}_dictionary.dict")
        lda_model = LdaModel.load(lda_model_path)
        dictionary = Dictionary.load(dictionary_path)

        # Load phân phối chủ đề của tài liệu
        material_file_path = os.path.join(DATA_DIR, f"eval_{subject}.pkl")
        with open(material_file_path, 'rb') as f:
            course_results = load(f)

        # Liên kết bài post với tài liệu tương ứng
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
        post_id = data.get("post_id")
        post_data = get_post_information(post_id)
        title = post_data["title"]
        description = post_data["description"]
        tags = post_data["tags"] # Danh sách các tag của bài post
        subject = post_data["subject"]
        
        if not title or not description:
            return jsonify({"error": "Thiếu tiêu đề hoặc mô tả"}), 400
        
        # Load model LDA + từ điển của môn học tương ứng
        lda_model_path = os.path.join(MODELS_DIR, f"{subject}_lda.model")
        dictionary_path = os.path.join(MODELS_DIR, f"{subject}_dictionary.dict")
        lda_model = LdaModel.load(lda_model_path)
        dictionary = Dictionary.load(dictionary_path)
        
        # Tiền xử lý bài post mới
        preprocessed_post = preprocess_string(title) + preprocess_string(description)
        for tag in tags:
            preprocessed_post += preprocess_string(tag)
        
        # Tính phân phối chủ đề của bài post mới
        new_post_dist = get_post_distribution(preprocessed_post, dictionary, lda_model)
        
        # Lấy tất cả bài post 
        all_posts = get_all_posts_by_subject(subject)

        # So sánh bài post mới và từng bài post đã có
        similar_posts = []
        for post_id, title, description, tags, input, expected, name in all_posts:
            # Preprocess bài post cũ
            preprocessed_post = preprocess_string(title) + preprocess_string(description)
            if tags[0] != None:
                for tag in tags:
                    preprocessed_post += preprocess_string(tag)
            post_dist = get_post_distribution(preprocessed_post, dictionary, lda_model)

            # Tính độ tương tự cosine, nếu cosine-similarity > 0.9 thì thêm bài post vào danh sách bài post tương tự
            sim = compute_cosine_similarity(np.array(new_post_dist).ravel(), np.array(post_dist).ravel())
            if sim >= 0.9:
                similar_posts.append({
                    "post_id": post_id,
                    "title": title,
                    "similarity": round(float(sim), 3),
                    "description": description,
                    "input": input,
                    "expected": expected,
                    "author": name
                })
                
        if len(similar_posts) > 0:
            similar_posts.sort(key=lambda x: x["similarity"], reverse=True)
            return jsonify({
                "similar_posts": similar_posts
            })
        else:
            return jsonify({"error": "Không tìm thấy bài viết tương đồng"}), 404
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@app.route('/related_post', methods=['POST'])
def related_post():
    try:
        data = request.get_json()
        post_id = data.get("post_id")
        post_data = get_post_information(post_id)
        title = post_data["title"]
        description = post_data["description"]
        tags = post_data["tags"] # Danh sách các tag của bài post
        subject = post_data["subject"]
        
        if not title or not description:
            return jsonify({"error": "Thiếu tiêu đề hoặc mô tả"}), 400
        
        # Load model LDA + từ điển của môn học tương ứng
        lda_model_path = os.path.join(MODELS_DIR, f"{subject}_lda.model")
        dictionary_path = os.path.join(MODELS_DIR, f"{subject}_dictionary.dict")
        lda_model = LdaModel.load(lda_model_path)
        dictionary = Dictionary.load(dictionary_path)
        
        # Tiền xử lý bài post mới
        preprocessed_post = preprocess_string(title) + preprocess_string(description)
        for tag in tags:
            preprocessed_post += preprocess_string(tag)
        
        # Tính phân phối chủ đề của bài post mới
        new_post_dist = get_post_distribution(preprocessed_post, dictionary, lda_model)
        
        # Lấy tất cả bài post 
        all_posts = get_all_posts_by_subject(subject, post_id)
        if len(all_posts) == 0:
            return jsonify({"error": "Không tìm thấy bài viết liên quan"}), 404
        
        threshold = 0.5

        # So sánh bài post mới và từng bài post đã có
        similar_posts = []
        posts = []
        for post_id, title, description, tags, input, expected, name in all_posts:
            # Preprocess bài post cũ
            preprocessed_post = preprocess_string(title) + preprocess_string(description)
            if tags[0] != None:
                for tag in tags:
                    preprocessed_post += preprocess_string(tag)
            post_dist = get_post_distribution(preprocessed_post, dictionary, lda_model)

            # Tính độ tương tự cosine
            sim = compute_cosine_similarity(np.array(new_post_dist).ravel(), np.array(post_dist).ravel())
            posts.append((post_id, title, round(float(sim), 3), description, input, expected, name))
        
        # Sắp xếp tất cả kết quả theo similarity giảm dần
        posts.sort(key=lambda x: x[2], reverse=True)
        # Xác định số lượng bài viết lấy trung bình (tối đa 10)
        top_k = min(10, len(posts))
        posts = posts[:top_k]
        sum = sum(item[2] for item in posts)
        avg_sim = sum/top_k
        
        if avg_sim > threshold:
            threshold = avg_sim

        for post in posts:
            if post[2] >= threshold:
                similar_posts.append({
                    "post_id": post[0],
                    "title": post[1],
                    "similarity": post[2],
                    "description": post[3],
                    "input": post[4],
                    "expected": post[5],
                    "author": post[6]
                })
        
        if len(similar_posts) > 0:
            return jsonify({
                "similar_posts": similar_posts
            })
        else:
            return jsonify({"error": "Không tìm thấy bài viết liên quan"}), 404
                
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    
@app.route('/translate_post', methods=['POST'])
def translate_post():
    try:
        data = request.get_json()
        post_id = data.get("post_id")
        success = translate_and_update_post(post_id)
                
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#  Chạy Flask server tại cổng 5000
#  app.run(host="0.0.0.0", port=5000, debug=True)