from gensim.corpora.dictionary import Dictionary
from gensim.models import LdaModel, TfidfModel
import os
import json
from pickle import dump

def extract_course_texts_mapping(course_vocabulary):
    mapping = {}
    course_texts = []
    for course_name, chapter in course_vocabulary.items():
        for chapter_name, items in chapter.items():
            for item_name, document_words in items.items():
                if document_words:
                    course_mapping = mapping.get("course", {})
                    course_map_vals = course_mapping.get(course_name, [])
                    course_map_vals.append(len(course_texts))
                    course_mapping[course_name] = course_map_vals
                    mapping["course"] = course_mapping

                    chapter_mapping = mapping.get("chapters", {})
                    chapter_map_vals = chapter_mapping.get(chapter_name, [])
                    chapter_map_vals.append(len(course_texts))
                    chapter_mapping[chapter_name] = chapter_map_vals
                    mapping["chapters"] = chapter_mapping

                    item_mapping = mapping.get("sections", {})
                    item_map_vals = item_mapping.get(item_name, [])
                    item_map_vals.append(len(course_texts))
                    item_mapping[item_name] = item_map_vals
                    mapping["sections"] = item_mapping

                    course_texts.append(document_words)
    return course_texts, mapping

def build_lda_models(course_corpus, course_dictionary, mapping, course_texts):
    # ==== Train Unsupervised LDA ====
    lda_model = LdaModel(
        corpus=course_corpus,
        num_topics= 30,
        id2word=course_dictionary
    )
    return lda_model

def eval_material(course_texts, course_corpus, lda_model):
    material_results = {}
    for course_doc_idx in range(0, len(course_texts)):
        idx_course_corpus = course_corpus[course_doc_idx]
        chunk = (idx_course_corpus, )
        lda_c_gamma = lda_model.inference(chunk=chunk)[0]
        idx_course_texts = course_texts[course_doc_idx]

        material_results[course_doc_idx] = {
            "lda": lda_c_gamma
        }
        
    return material_results

course_name = 'DSA'  # Thay thế với tên môn học cần xử lý
course_json_path = f"preprocessed_{course_name}.json"  

with open(course_json_path, 'r', encoding='utf-8') as f:
    course_vocabulary = json.load(f)
    
course_texts, mapping = extract_course_texts_mapping(course_vocabulary)
# print(course_texts)
# print(mapping)

course_dictionary = Dictionary(course_texts)
# print(course_dictionary)
# print(course_dictionary.token2id)

course_corpus = [course_dictionary.doc2bow(text) for text in course_texts]
# print(course_corpus)

lda_model = build_lda_models(course_corpus, course_dictionary, mapping, course_texts)
models = {}
models[course_name] = {
        "model": lda_model,
        "dictionary": course_dictionary,
        "corpus": course_corpus
    }

output_dir = "models"
os.makedirs(output_dir, exist_ok=True)

for course_name, model_data in models.items():
    model_data["model"].save(f"{output_dir}/{course_name}_lda.model")
    model_data["dictionary"].save(f"{output_dir}/{course_name}_dictionary.dict")
    
material_results = eval_material(course_texts, course_corpus, lda_model)
# print(material_results)

output_dir = "data"
os.makedirs(output_dir, exist_ok=True)

output_eval_file = os.path.join(output_dir, f"eval_{course_name}.pkl")
with open(output_eval_file, 'wb') as f:
    dump({
        "mapping": mapping,
        "material_results": material_results
    }, f)
    