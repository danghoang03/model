import google.generativeai as genai
import os
import psycopg2
import traceback
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
        translation_model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
        print("Đã cấu hình thành công Gemini API.")
    except Exception as e:
        print(f"Lỗi khi cấu hình Gemini API: {e}")
        translation_model = None # Không thể sử dụng model
        
def translate_text_gemini(text_to_translate, model):
    """Sử dụng Gemini model để dịch văn bản từ tiếng Việt sang tiếng Anh."""
    if not model:
        print("Lỗi: Model dịch chưa được khởi tạo.")
        return None
    if not text_to_translate or not isinstance(text_to_translate, str):
        print("Cảnh báo: Đầu vào không phải là văn bản hợp lệ để dịch.")
        return None 

    prompt = f"Translate the following Vietnamese text to English. Output only the translated text, without any introductory phrases or explanations:\n\nVietnamese: \"{text_to_translate}\"\n\nEnglish:"

    try:
        # Sử dụng generate_content thay vì chat session cho tác vụ đơn giản
        response = model.generate_content(prompt)
        # response.text thường chứa kết quả dịch trực tiếp nếu prompt rõ ràng
        translated_text = response.text.strip()
        return translated_text
    except Exception as e:
        print(f"Lỗi trong quá trình dịch bằng Gemini: {e}")
        traceback.print_exc()
        return None # Trả về None nếu có lỗi
    
def translate_and_update_post(post_id):
    """
    Dịch tiêu đề và mô tả của bài viết sang tiếng Anh bằng Gemini
    và cập nhật vào cơ sở dữ liệu.
    """
    if not translation_model:
         print(f"Bỏ qua dịch cho post ID {post_id} do lỗi khởi tạo model.")
         return False
     
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    query = """
        SELECT title, description FROM posts WHERE id = %s;
    """
    cursor.execute(query, (post_id,))
    result = cursor.fetchone()
    vietnamese_title, vietnamese_description = result
    
    # Dịch tiêu đề
    title_en = translate_text_gemini(vietnamese_title, translation_model)
    if title_en:
        print(f"  -> Tiêu đề gốc: {vietnamese_title}")
        print(f"  -> Tiêu đề EN: {title_en}")
    else:
        print(f"  -> Lỗi dịch tiêu đề hoặc tiêu đề gốc không hợp lệ.")

    # Dịch mô tả
    description_en = translate_text_gemini(vietnamese_description, translation_model)
    if description_en:
        # In một phần để tránh log quá dài
        print(f"  -> Mô tả gốc: {vietnamese_description[:100]}...")
        print(f"  -> Mô tả EN: {description_en[:100]}...")
    else:
        print(f"  -> Lỗi dịch mô tả hoặc mô tả gốc không hợp lệ.")

    if title_en and description_en: # Hoặc if title_en and description_en:
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
        return True
    else:
        print(f"  -> Không có bản dịch hợp lệ nào để cập nhật cho post ID: {post_id}")
        return False
    return False

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