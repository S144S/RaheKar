from openai import OpenAI
import json

client = OpenAI(base_url='https://api.gapgpt.app/v1', api_key="sk-TgPTWJVFuKzZOkLKdxO1NEhUhsrua7BbKyrdJc8l8X1yYV99")

def extract_json(text: str) -> str:

    text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}") + 1

    if start == -1 or end == -1:
        raise ValueError("JSON not found in response")

    return text[start:end]


def get_job_info(job_title):

    prompt = f"""
شما یک مشاور شغلی هستید.

ازت میخوام یک توضیح کامل و حرفه ای راجع به عنوان شغلی زیر بدی که حتما شامل موارد
توضیحات
درآمد
مزایا
باشد

عنوان شغل: {job_title}

هیچ توضیح اضافه ای نده، بلافاصله متن اصلی رو شروع کن
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    content = response.choices[0].message.content

    try:
        result = content
        return result
    except:
        return {"error": "مدل JSON معتبر برنگرداند", "raw": content}


def get_job_path(job_title: str) -> dict:

    prompt = f"""
فقط یک JSON معتبر برگردان. هیچ متن دیگر ننویس.

دستور:
برای شغل "{job_title}" یک مسیر یادگیری و پیشرفت شغلی در **۱۰ گام** تولید کن.
گام‌ها باید از دوران دبیرستان نوبت اول (پایه) شروع شوند و تا سطح حرفه‌ای ادامه پیدا کنند.

ساختار JSON دقیقاً باید به این شکل باشد:

{{
  "step1": "گام اول ...",
  "step2": "گام دوم ...",
  "step3": "گام سوم ...",
  "step4": "گام چهارم ...",
  "step5": "گام پنجم ...",
  "step6": "گام ششم ...",
  "step7": "گام هفتم ...",
  "step8": "گام هشتم ...",
  "step9": "گام نهم ...",
  "step10": "گام دهم ..."
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "Return ONLY JSON. No explanation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )

        raw = response.choices[0].message.content
        json_text = extract_json(raw)

        return json.loads(json_text)

    except Exception as e:
        return {"error": str(e)}


def ask_job_ai(job_title, question):
    prompt = f"به عنوان یک متخصص شغلی، به این پرسش درباره شغل {job_title} نهایتا در 2 پاراگراف بده:\n{question}"
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "system", "content": "شما یک کارشناس شغلی فارسی هستید."},
                  {"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content


def job_recommendation(info):
    prompt = f"""
تو یک مشاور شغلی فارسی حرفه ای هستی.

من یک آزمون از کاربر گرفتم و نتایج آزمون رو برات در زیر گذاشتم:
{info}

ازت میخوام متناسب ترین شغل برای کاربر رو فقط با آوردن اسم اون شغل بدون هیچ توضیح اضافی و هیچ کلمه انگلیسی بدی.
همچنین ارت میخوام  که شغل جدید اختراع نکنی و از شغل های موجود در دنیا استفاده کنی.
"""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "system", "content": "شما یک کارشناس شغلی فارسی هستید."},
                  {"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content


if __name__ == "__main__":

    job = input("عنوان شغل را وارد کنید: ")

    print("\n--- مسیر شغلی ده‌گامی ---")
    path = get_job_path(job)
    print(json.dumps(path, ensure_ascii=False, indent=2))