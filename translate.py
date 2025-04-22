import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
import os
import psycopg2
import traceback
import random
import time
from dotenv import load_dotenv

DB_CONFIG = {
    "dbname": "tc-sharing",
    "user": "postgres",
    "password": "123456",
    "host": "localhost",
    "port": "5432"
}

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Lỗi: Vui lòng đặt biến môi trường GEMINI_API_KEY")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        translation_model = genai.GenerativeModel('gemini-2.0-flash-lite')
        print("Đã cấu hình thành công Gemini API.")
    except Exception as e:
        print(f"Lỗi khi cấu hình Gemini API: {e}")
        translation_model = None # Không thể sử dụng model
        
def translate_text_gemini(text_to_translate, model):
    """Sử dụng Gemini model để dịch văn bản từ tiếng Việt sang tiếng Anh."""
    if not model:
        'error', "Model dịch chưa được khởi tạo."
        return None

    prompt = f"Translate the following Vietnamese text to English. Output only the translated text, without any introductory phrases or explanations:\n\nVietnamese: \"{text_to_translate}\"\n\nEnglish:"
    max_retries=3
    base_wait_time=1
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            translated_text = response.text.strip()
            print(f"    -> Dịch thành công (lần thử {attempt + 1})")
            return 'success', translated_text
        except ResourceExhausted as e:
            print(f"    -> Gặp lỗi Rate Limit (429) ở lần thử {attempt + 1}/{max_retries}.")
            if attempt < max_retries - 1:
                # Tính thời gian chờ (exponential backoff + random jitter)
                wait_time = (base_wait_time * (2 ** attempt)) + random.uniform(0.1, 0.5)
                print(f"    -> Chờ {wait_time:.2f} giây trước khi thử lại...")
                time.sleep(wait_time)
            else:
                print("    -> Đã hết số lần thử lại cho lỗi Rate Limit.")
                return 'rate_limit_exceeded', f"API rate limit exceeded after {max_retries} retries: {e}"

        except Exception as e:
            print(f"    -> Lỗi không xác định khi dịch ở lần thử {attempt + 1}: {e}")
            traceback.print_exc()
            # Không thử lại với lỗi không xác định
            return 'error', f"Lỗi dịch không xác định: {e}"
    
def translate_and_update_post(post_id):
    """
    Dịch tiêu đề và mô tả của bài viết sang tiếng Anh bằng Gemini
    và cập nhật vào cơ sở dữ liệu.
    """
    if not translation_model:
        return 'error', "Model dịch chưa sẵn sàng."
     
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    query = """
        SELECT title, description FROM posts WHERE id = %s;
    """
    cursor.execute(query, (post_id,))
    result = cursor.fetchone()
    vietnamese_title, vietnamese_description = result
    
    # Dịch tiêu đề
    title_status, title_en = translate_text_gemini(vietnamese_title, translation_model)
    desc_status, description_en = translate_text_gemini(vietnamese_description, translation_model)
    if title_status == 'rate_limit_exceeded' or desc_status == 'rate_limit_exceeded':
            cursor.close()
            conn.close()
            return 'rate_limit', "API rate limit exceeded during translation."
        
    if title_status == 'error' or desc_status == 'error':
            # Có thể lấy message lỗi chi tiết hơn từ title_en hoặc description_en nếu cần
            cursor.close()
            conn.close()
            return 'translation_error', "Error occurred during translation process."

    if title_en and description_en:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = """
            UPDATE posts
            SET title_en = %s, description_en = %s
            WHERE id = %s;
        """
        cursor.execute(query, (title_en, description_en, post_id))
        conn.commit() # Lưu thay đổi
        cursor.close()
        return 'success', f"Successfully translated and updated post ID {post_id}."
    else:
        return 'no_change', f"No valid translations to update for post ID {post_id}."

# if __name__ == '__main__':
#     example_post_id = 1

#     if not GEMINI_API_KEY or not translation_model:
#          print("Vui lòng kiểm tra cấu hình API Key và khởi tạo model.")
#     else:
#          success = translate_and_update_post(example_post_id)
#          if success:
#              print("\nHoàn thành cập nhật bản dịch.")
#          else:
#              print("\nCập nhật bản dịch không thành công hoặc không có gì thay đổi.")