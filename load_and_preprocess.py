import json
import os
from gensim.parsing.preprocessing import preprocess_string

def load_and_preprocess(subject_json_path, subject_name):
    """
    Đọc file JSON của môn học và tiền xử lý nội dung.
    Lưu kết quả vào file preprocessed_{subject_name}.json.
    """
    
    with open(subject_json_path, 'r', encoding='utf-8') as f:
        subject_data = json.load(f)

    preprocessed_data = {}

    for course, chapters in subject_data.items():
        preprocessed_data[course] = {}

        for chapter, sections in chapters.items():
            preprocessed_data[course][chapter] = {}

            for section, content in sections.items():
                cleaned_content = preprocess_string(content)
                preprocessed_data[course][chapter][section] = cleaned_content

    output_file_path = f"preprocessed_{subject_name}.json"
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(preprocessed_data, f, ensure_ascii=False, indent=4)


subject_name = 'DSA'  # Thay thế với tên môn học cần xử lý
subject_json_path = f"{subject_name}.json"  

load_and_preprocess(subject_json_path, subject_name)