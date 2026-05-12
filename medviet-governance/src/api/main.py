# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về raw patient data (chỉ admin được phép).
    Load từ data/raw/patients_raw.csv
    Trả về 10 records đầu tiên dưới dạng JSON.
    """
    try:
        df = pd.read_csv("data/raw/patients_raw.csv")
        # Điền NaN bằng None để FastAPI có thể parse ra JSON hợp lệ
        df = df.where(pd.notnull(df), None)
        return df.head(10).to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Raw data file not found.")

# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về anonymized data (ml_engineer và admin được phép).
    Load raw data → anonymize → trả về JSON.
    """
    try:
        df = pd.read_csv("data/raw/patients_raw.csv")
        df_anon = anonymizer.anonymize_dataframe(df)
        df_anon = df_anon.where(pd.notnull(df_anon), None)
        
        # Thường dữ liệu train sẽ cần nhiều hơn 10 dòng, 
        # nhưng để test API nhanh bạn có thể trả về 50 hoặc toàn bộ.
        return df_anon.to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Raw data file not found.")

# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về aggregated metrics (data_analyst, ml_engineer, admin).
    Ví dụ: số bệnh nhân theo từng loại bệnh (không có PII).
    """
    try:
        df = pd.read_csv("data/raw/patients_raw.csv")
        
        # Đếm số lượng bệnh nhân theo cột "benh"
        disease_counts = df["benh"].value_counts().reset_index()
        disease_counts.columns = ["loai_benh", "so_luong"]
        
        return disease_counts.to_dict(orient="records")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Raw data file not found.")
    except KeyError:
        raise HTTPException(status_code=500, detail="Column 'benh' not found in dataset.")

# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Chỉ admin được xóa. Các role khác nhận 403.
    """
    # Trong môi trường Lab không kết nối Database thật,
    # chúng ta chỉ cần trả về thông báo giả lập thành công.
    # Casbin Enforcer ở decorator đã chặn đứng những người không phải Admin rồi.
    return {
        "status": "success",
        "message": f"Patient with ID {patient_id} has been deleted.",
        "deleted_by": current_user["username"]
    }

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}