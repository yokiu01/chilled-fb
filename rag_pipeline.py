import os
# LLM
from langchain_google_genai import ChatGoogleGenerativeAI
# Chain (오류 해결을 위한 우회 경로 적용)
from langchain_community.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# 임베딩 및 벡터스토어
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# 이전 단계에서 정의된 로드 및 분할 함수 (같은 파일에 있다고 가정)
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

# --- 환경 설정 ---
KB_DIR = "KB-Dance-History"
CHROMA_DB_PATH = "./chroma_db"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

def load_and_split_documents(kb_dir: str) -> list[Document]:
    """문서 로드 및 청크 분할을 담당합니다."""
    print(f"[{KB_DIR}] 폴더에서 텍스트 파일을 로드합니다...")
    loader = DirectoryLoader(
        path=kb_dir,
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"}
    )
    documents = loader.load()
    print(f"총 {len(documents)}개의 문서가 로드되었습니다.")

    for doc in documents:
        base_name = os.path.basename(doc.metadata['source'])
        parts = os.path.splitext(base_name)[0].split('-')
        if len(parts) >= 3:
            doc.metadata['분류'] = parts[0]
            doc.metadata['주제'] = parts[1]
            doc.metadata['출처'] = parts[2]
            
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )
    
    split_docs = text_splitter.split_documents(documents)
    print(f"총 문서가 {len(split_docs)}개의 청크(Chunk)로 분할되었습니다.")
    return split_docs


def setup_vector_store(kb_dir: str, db_path: str):
    """문서를 로드, 분할하고 임베딩하여 벡터 데이터베이스에 저장합니다."""
    print("문서 로드 및 청크 분할을 시작합니다...")
    chunks = load_and_split_documents(kb_dir)
    print("문서 분할 완료.")
    
    # 2. 임베딩 모델 설정
    print("임베딩 모델을 로드합니다...")
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    # 3. ChromaDB에 저장 (임베딩 실행)
    print("청크를 벡터로 변환하고 ChromaDB에 저장합니다...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=db_path  # 로컬에 DB 파일 생성
    )
    
    # DB 파일이 저장되도록 강제로 디스크에 기록
    vectorstore.persist()
    print(f"✅ 벡터 데이터베이스가 성공적으로 구축되었습니다. 저장 경로: {db_path}")

    return vectorstore


if __name__ == "__main__":
    # 1. Chroma DB 구축 및 로드
    vector_db = setup_vector_store(KB_DIR, CHROMA_DB_PATH) 
    
    # 2. LLM 설정 (Gemini 사용)
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0             
    )
    
    # 3. 프롬프트 템플릿 정의
    template = """
    당신은 한국무용과 전통문화에 대한 전문 지식 멘토 '춤마루 프로젝트'의 AI 어시스턴트입니다.
    제공된 [맥락(Context)] 정보를 바탕으로 사용자 질문에 대해 전문적이고 정확하게 답변해 주세요.
    만약 제공된 맥락 정보만으로는 답변이 불가능하다면, '제공된 자료만으로는 답변하기 어렵습니다'라고 응답하세요.
    
    [맥락(Context)]:
    {context}
    
    [질문]:
    {question}
    
    [답변]:
    """
    
    RAG_PROMPT = PromptTemplate(
        template=template, input_variables=["context", "question"]
    )
    
    # 4. RetrievalQA Chain 구축
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": RAG_PROMPT}
    )
    
    # 5. RAG 시스템 최종 테스트
    print("\n\n--- 춤마루 RAG 시스템 최종 답변 테스트 (Gemini) ---")
    
    test_query = "대삼소삼 기법에서 이매방 춤과 민속장단의 용어 차이는 무엇이며, 호흡 구조는 어떠합니까?"
    
    result = qa_chain.invoke({"query": test_query})
    
    print(f"**[사용자 질문]**: {test_query}")
    print("-" * 50)
    print(f"**[AI 답변]**: {result['result']}")
    
    # 답변에 사용된 출처 정보 출력
    print("\n**[참조된 원본 데이터]**")
    for doc in result['source_documents']:
        print(f"- 출처: {doc.metadata.get('출처', '정보 없음')} ({doc.metadata.get('주제', '정보 없음')})")
    print("-" * 50)