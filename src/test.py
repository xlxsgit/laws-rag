# src/test_gemini.py
import google.generativeai as genai
from config import GEMINI_API_KEY


def test_gemini():
    """测试Gemini API调用"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)

        # 使用你列表中实际存在的模型
        model = genai.GenerativeModel('gemini-2.0-flash')

        response = model.generate_content("请用一句话介绍你自己")

        print("✅ Gemini调用成功!")
        print(f"回复: {response.text}")
        return True

    except Exception as e:
        print(f"❌ Gemini调用失败: {e}")
        return False


if __name__ == "__main__":
    test_gemini()