from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import os
import shutil
import logging
import traceback

from ..models.database import get_db
from ..services.data_processor import DataProcessor
from ..config.settings import settings

router = APIRouter(prefix="/data", tags=["数据管理"])
logger = logging.getLogger(__name__)


class DataImportResponse(BaseModel):
    success: bool
    message: str
    records_imported: int = 0
    errors: List[str] = []
    warnings: List[str] = []
    quality_report: Optional[Dict[str, Any]] = None


class DataValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str] = []


@router.post("/import/csv", response_model=DataImportResponse)
async def import_csv_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    logger.info(f"开始导入CSV文件: {file.filename}")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支持CSV文件")
    
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"文件已保存: {file_path}")
        
        processor = DataProcessor(db)
        
        logger.info("开始加载CSV数据...")
        df = processor.load_csv_data(file_path)
        logger.info(f"加载完成，共{len(df)}行数据")
        
        logger.info("开始数据清洗...")
        df = processor.clean_data(df)
        logger.info(f"清洗完成，剩余{len(df)}行数据")
        
        logger.info("开始数据标准化...")
        df = processor.standardize_data(df)
        logger.info("标准化完成")
        
        logger.info("开始数据验证...")
        is_valid, errors, warnings = processor.validate_data(df)
        
        if not is_valid:
            logger.error(f"数据验证失败: {errors}")
            return DataImportResponse(
                success=False,
                message="数据验证失败",
                errors=errors,
                warnings=warnings
            )
        
        logger.info("开始导入数据库...")
        import_result = processor.import_to_database(df, batch_size=500)
        
        if import_result["success"]:
            logger.info(f"导入完成，共{import_result['records_imported']}条记录")
            return DataImportResponse(
                success=True,
                message=f"成功导入{import_result['records_imported']}条数据",
                records_imported=import_result['records_imported'],
                warnings=warnings,
                quality_report=import_result.get("quality_report")
            )
        else:
            logger.error(f"导入失败: {import_result.get('error')}")
            return DataImportResponse(
                success=False,
                message=f"导入失败: {import_result.get('error')}",
                errors=[import_result.get('error')],
                warnings=warnings,
                quality_report=import_result.get("quality_report")
            )
    except Exception as e:
        error_msg = f"数据导入失败: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return DataImportResponse(
            success=False,
            message=error_msg,
            errors=[str(e)]
        )


@router.post("/import/excel", response_model=DataImportResponse)
async def import_excel_data(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    logger.info(f"开始导入Excel文件: {file.filename}")
    
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件(.xlsx, .xls)")
    
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"文件已保存: {file_path}")
        
        import pandas as pd
        processor = DataProcessor(db)
        
        logger.info("开始加载Excel数据...")
        df = pd.read_excel(file_path)
        logger.info(f"加载完成，共{len(df)}行数据")
        
        logger.info("开始数据清洗...")
        df = processor.clean_data(df)
        logger.info(f"清洗完成，剩余{len(df)}行数据")
        
        logger.info("开始数据标准化...")
        df = processor.standardize_data(df)
        logger.info("标准化完成")
        
        logger.info("开始数据验证...")
        is_valid, errors, warnings = processor.validate_data(df)
        
        if not is_valid:
            logger.error(f"数据验证失败: {errors}")
            return DataImportResponse(
                success=False,
                message="数据验证失败",
                errors=errors,
                warnings=warnings
            )
        
        logger.info("开始导入数据库...")
        import_result = processor.import_to_database(df, batch_size=500)
        
        if import_result["success"]:
            logger.info(f"导入完成，共{import_result['records_imported']}条记录")
            return DataImportResponse(
                success=True,
                message=f"成功导入{import_result['records_imported']}条数据",
                records_imported=import_result['records_imported'],
                warnings=warnings,
                quality_report=import_result.get("quality_report")
            )
        else:
            logger.error(f"导入失败: {import_result.get('error')}")
            return DataImportResponse(
                success=False,
                message=f"导入失败: {import_result.get('error')}",
                errors=[import_result.get('error')],
                warnings=warnings,
                quality_report=import_result.get("quality_report")
            )
    except Exception as e:
        error_msg = f"数据导入失败: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return DataImportResponse(
            success=False,
            message=error_msg,
            errors=[str(e)]
        )


@router.get("/buildings")
async def get_buildings_list(db: Session = Depends(get_db)):
    processor = DataProcessor(db)
    buildings = processor.get_buildings_list()
    return {"buildings": buildings, "total": len(buildings)}


@router.get("/meters")
async def get_meters_list(db: Session = Depends(get_db)):
    processor = DataProcessor(db)
    meters = processor.get_meters_list()
    return {"meters": meters, "total": len(meters)}


@router.get("/date-range")
async def get_date_range(
    building_id: Optional[str] = Query(None, description="建筑ID"),
    db: Session = Depends(get_db)
):
    processor = DataProcessor(db)
    date_range = processor.get_date_range(building_id)
    return date_range


@router.get("/summary")
async def get_data_summary(
    building_id: Optional[str] = Query(None, description="建筑ID"),
    db: Session = Depends(get_db)
):
    processor = DataProcessor(db)
    summary = processor.get_data_summary(building_id)
    
    # 获取基础统计信息
    from ..models.database import EnergyData
    from sqlalchemy import func
    
    query = db.query(EnergyData)
    if building_id:
        query = query.filter(EnergyData.building_id == building_id)
    
    total_records = query.count()
    total_buildings = db.query(func.count(func.distinct(EnergyData.building_id))).scalar()
    total_meters = db.query(func.count(func.distinct(EnergyData.meter_id))).scalar()
    
    date_range = db.query(
        func.min(EnergyData.timestamp).label('min_date'),
        func.max(EnergyData.timestamp).label('max_date')
    ).first()
    
    return {
        "total_records": total_records,
        "total_buildings": total_buildings,
        "total_meters": total_meters,
        "date_range": {
            "start": date_range.min_date.isoformat() if date_range.min_date else None,
            "end": date_range.max_date.isoformat() if date_range.max_date else None
        },
        **summary
    }


@router.get("/data")
async def get_data(
    building_id: Optional[str] = Query(None, description="建筑ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(1000, ge=1, le=10000, description="每页记录数"),
    db: Session = Depends(get_db)
):
    processor = DataProcessor(db)
    result = processor.get_data_with_pagination(building_id, page, page_size)
    return result


@router.get("/aggregated")
async def get_aggregated_data(
    building_id: Optional[str] = Query(None, description="建筑ID"),
    interval: str = Query("day", description="聚合间隔：day, week, month, year"),
    db: Session = Depends(get_db)
):
    processor = DataProcessor(db)
    result = processor.get_aggregated_data(building_id, interval)
    return result


@router.post("/validate")
async def validate_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """验证数据文件"""
    logger.info(f"开始验证文件: {file.filename}")
    
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        processor = DataProcessor(db)
        
        if file.filename.endswith('.csv'):
            df = processor.load_csv_data(file_path)
        elif file.filename.endswith(('.xlsx', '.xls')):
            import pandas as pd
            df = pd.read_excel(file_path)
        else:
            raise HTTPException(status_code=400, detail="只支持CSV和Excel文件")
        
        df = processor.clean_data(df)
        df = processor.standardize_data(df)
        is_valid, errors, warnings = processor.validate_data(df)
        
        quality_report = processor.generate_quality_report(df)
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "quality_report": quality_report
        }
    except Exception as e:
        error_msg = f"验证失败: {str(e)}"
        logger.error(error_msg)
        return {
            "is_valid": False,
            "errors": [str(e)],
            "warnings": [],
            "quality_report": None
        }
