import openai
from jinja2 import Environment, FileSystemLoader
import os
import uuid
from dotenv import load_dotenv


# Jinja2 템플릿 로더 설정
template_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'prompts')
env = Environment(loader=FileSystemLoader(template_dir))


class AzureOpenAIService:
    def __init__(self, endpoint, key, dep_curriculum, dep_embed):
        dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        load_dotenv(dotenv_path)
        openai.api_type = "azure"
        openai.api_base = endpoint
        openai.api_version = "2024-05-01-preview"
        openai.api_key = key
        os.environ["AZURE_OPENAI_API_KEY"] = key
        self.dep_curriculum = dep_curriculum
        self.dep_embed = dep_embed

    def get_initial_curriculum(self, profile):
        """아동 프로필 기반 초기 학습 주제 생성"""
        tmpl = env.get_template("initial_curriculum.txt")
        return tmpl.render(
            name=profile.name,
            age=profile.age,
            interests=profile.interests
        )

    def get_embedding(self, text: str) -> list:
        """텍스트를 임베딩 벡터로 변환"""
        if openai.api_type == "azure":
            response = openai.embeddings.create(
                input=text,
                model=self.dep_embed
            )
        else:
            response = openai.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )
        embedding = response.data[0].embedding
        return embedding

    def generate_materials(self, curriculum_text: str, docs: list):
        """커리큘럼 및 유사 자료를 바탕으로 교재 및 평가 문제 생성"""
        tmpl = env.get_template("materials.txt")
        prompt = tmpl.render(curriculum=curriculum_text, docs=docs)
        resp = openai.chat.completions.create(
            model=self.dep_curriculum,
            messages=[
                {"role": "system", "content": "교재 생성 AI"},
                {"role": "user",   "content": prompt}
            ]
        )
        content = resp.choices[0].message.content.strip()
        
        # 문제와 정답을 분리
        parts = content.split("---정답---")
        lesson = parts[0].strip()  # 지문과 문제
        answers = parts[1].strip() if len(parts) > 1 else ""  # 정답
        
        # materials에는 정답만 포함 (피드백용)
        materials = [answers] if answers else []
        return lesson, materials

    def save_lesson(self, child_id, lesson_text, docs):
        """학습 세션 ID 생성 및 저장"""
        lesson_id = str(uuid.uuid4())
        # TODO: 필요 시 저장 로직 추가
        return lesson_id

    def create_feedback(self, materials_text, responses_text):
        tmpl = env.get_template("feedback.txt")
        prompt = tmpl.render(materials_text=materials_text, responses_text=responses_text)
        resp = openai.chat.completions.create(
            model=self.dep_curriculum,
            messages=[
                {"role": "system", "content": "피드백 생성 AI"},
                {"role": "user",   "content": prompt}
            ]
        )
        return resp.choices[0].message.content.strip()

    def generate_next_material(self, child_id, lesson_id, last_responses=None):
        """이전 학습 반영하여 다음 교재 생성"""
        tmpl = env.get_template("next_material.txt")
        prompt = tmpl.render(child_id=child_id, lesson_id=lesson_id, last_responses=last_responses)
        resp = openai.chat.completions.create(
            model=self.dep_curriculum,
            messages=[
                {"role": "system", "content": "다음 교재 생성 AI"},
                {"role": "user",   "content": prompt}
            ]
        )
        return resp.choices[0].message.content.strip()

    def create_overall_feedback(self, name, age, history):
        """
        학습 이력 전체를 받아 종합 피드백을 LLM으로 생성
        history: [{interests, topic, feedback}, ...]
        """
        tmpl = env.get_template("feedback_summary.txt")
        prompt = tmpl.render(name=name, age=age, history=history)
        resp = openai.chat.completions.create(
            model=self.dep_curriculum,
            messages=[
                {"role": "system", "content": "종합 피드백 생성 AI"},
                {"role": "user",   "content": prompt}
            ]
        )
        return resp.choices[0].message.content.strip() 