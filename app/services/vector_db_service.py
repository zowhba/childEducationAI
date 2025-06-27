from chromadb import Client
import os
from app.services.azure_openai_service import AzureOpenAIService
import openai

class VectorDBService:
    def __init__(self, persist_directory):
        self.client = Client()
        self.collection = self.client.get_or_create_collection(name="learning")
        # self.dep_curriculum = os.getenv("AZURE_OPENAI_DEPLOY_CURRICULUM")  # Uncomment if needed

    def add_assessment(self, student_id: str, lesson_id: str, responses: list, azure_service):
        """학생의 평가 응답을 벡터DB에 저장"""
        embedding = azure_service.get_embedding(" ".join(responses))
        metadata = {"student_id": student_id, "lesson_id": lesson_id, "type": "assessment"}
        self.collection.add(
            documents=[" ".join(responses)],
            embeddings=[embedding],
            ids=[f"{student_id}_{lesson_id}_resp"],
            metadatas=[metadata]
        )

    def query_similar(self, embedding: list, top_k: int = 5) -> list:
        """유사 자료  조회"""
        res = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k
        )
        return list(zip(res['documents'], res['metadatas']))

    def create_feedback(self, prompt: str):
        resp = openai.chat.completions.create(
            model=self.dep_curriculum,
            messages=[
                {"role": "system", "content": "다음 교재 생성 AI"},
                {"role": "user",   "content": prompt}
            ]
        )
        # This method should return the response from the OpenAI chat completion
        return resp