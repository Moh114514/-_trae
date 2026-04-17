from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from ..models.database import get_db
from ..services.rag_service import KnowledgeBaseService, RAGService
from ..config.settings import settings

router = APIRouter(prefix="/intelligence", tags=["智慧运维"])


class QueryRequest(BaseModel):
    query: str
    k: int = 3


class AnomalyAnalysisRequest(BaseModel):
    building_id: str
    anomaly_data: Dict[str, Any]


class EquipmentQueryRequest(BaseModel):
    equipment_type: str


class EnergySavingRequest(BaseModel):
    building_type: str


knowledge_base = KnowledgeBaseService()
rag_service = RAGService(knowledge_base)


@router.post("/initialize-knowledge-base")
async def initialize_knowledge_base():
    try:
        knowledge_base.initialize_default_knowledge()
        return {"success": True, "message": "知识库初始化成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识库初始化失败: {str(e)}")


@router.post("/add-document")
async def add_document_to_knowledge_base(
    file: UploadFile = File(...),
    category: str = Query("general", description="文档类别"),
    tags: str = Query("", description="标签，用逗号分隔")
):
    upload_dir = settings.KNOWLEDGE_BASE_DIR
    import os
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    
    with open(file_path, "wb") as buffer:
        import shutil
        shutil.copyfileobj(file.file, buffer)
    
    metadata = {
        "category": category,
        "tags": tags.split(",") if tags else [],
        "filename": file.filename
    }
    
    success = knowledge_base.add_document(file_path, metadata)
    
    if success:
        return {"success": True, "message": f"文档 {file.filename} 添加成功"}
    else:
        raise HTTPException(status_code=500, detail="文档添加失败")


@router.post("/add-text")
async def add_text_to_knowledge_base(
    text: str = Query(..., description="要添加的文本内容"),
    category: str = Query("general", description="文本类别"),
    tags: str = Query("", description="标签，用逗号分隔")
):
    metadata = {
        "category": category,
        "tags": tags.split(",") if tags else []
    }
    
    success = knowledge_base.add_text(text, metadata)
    
    if success:
        return {"success": True, "message": "文本添加成功"}
    else:
        raise HTTPException(status_code=500, detail="文本添加失败")


@router.post("/search")
async def search_knowledge_base(request: QueryRequest):
    results = knowledge_base.search(request.query, k=request.k)
    return {
        "query": request.query,
        "results": results,
        "total": len(results)
    }


@router.post("/query")
async def intelligent_query(request: QueryRequest):
    result = rag_service.query_with_rag(request.query, k=request.k)
    
    # 使用预设回答
    answer = result.get('answer', f"基于知识库的回答：\n{result['context'][:500]}")
    
    return {
        "query": request.query,
        "answer": answer,
        "context": result['context'],
        "relevant_documents": result['relevant_documents']
    }


@router.post("/analyze-anomaly")
async def analyze_energy_anomaly(request: AnomalyAnalysisRequest):
    result = rag_service.analyze_energy_anomaly(
        request.building_id,
        request.anomaly_data
    )
    return result


@router.post("/equipment-status")
async def query_equipment_status(request: EquipmentQueryRequest):
    result = rag_service.query_equipment_status(request.equipment_type)
    return result


@router.post("/energy-saving-suggestions")
async def get_energy_saving_suggestions(request: EnergySavingRequest):
    result = rag_service.get_energy_saving_suggestions(request.building_type)
    return result


@router.get("/data-dictionary")
async def get_energy_data_dictionary():
    return knowledge_base.energy_data_dict


@router.get("/equipment-manuals")
async def get_equipment_manuals():
    return knowledge_base.equipment_manuals


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "knowledge_base": "initialized",
        "openai_configured": bool(settings.OPENAI_API_KEY)
    }


@router.get("/documents")
async def get_documents(
    category: Optional[str] = Query(None, description="文档类别"),
    limit: int = Query(100, description="返回文档数量限制")
):
    filter = {"category": category} if category else None
    documents = knowledge_base.get_documents(filter=filter, limit=limit)
    return {
        "documents": documents,
        "total": len(documents),
        "category": category
    }


@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    document = knowledge_base.get_document_by_id(document_id)
    if document:
        return document
    else:
        raise HTTPException(status_code=404, detail="文档不存在")


@router.get("/categories")
async def get_categories():
    categories = knowledge_base.get_categories()
    return {
        "categories": categories,
        "total": len(categories)
    }


@router.get("/tags")
async def get_tags():
    tags = knowledge_base.get_tags()
    return {
        "tags": tags,
        "total": len(tags)
    }


@router.post("/search-by-category")
async def search_by_category(
    category: str = Query(..., description="文档类别"),
    query: Optional[str] = Query(None, description="搜索关键词"),
    k: int = Query(5, description="返回结果数量")
):
    results = knowledge_base.search_by_category(category, query=query, k=k)
    return {
        "category": category,
        "query": query,
        "results": results,
        "total": len(results)
    }


@router.post("/search-by-tags")
async def search_by_tags(
    tags: str = Query(..., description="标签，用逗号分隔"),
    query: Optional[str] = Query(None, description="搜索关键词"),
    k: int = Query(5, description="返回结果数量")
):
    tag_list = tags.split(",") if tags else []
    results = knowledge_base.search_by_tags(tag_list, query=query, k=k)
    return {
        "tags": tag_list,
        "query": query,
        "results": results,
        "total": len(results)
    }
