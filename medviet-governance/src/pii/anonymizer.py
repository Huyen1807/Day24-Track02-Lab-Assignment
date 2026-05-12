# src/pii/anonymizer.py
import pandas as pd
import hashlib
import random
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")

class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        TODO: Anonymize text với strategy được chọn.

        Strategies:
        - "mask"    : Nguyen Van A → N****** V** A
        - "replace" : thay bằng fake data (dùng Faker)
        - "hash"    : SHA-256 one-way hash
        - "generalize": chỉ dùng cho tuổi/năm sinh
        """
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        # Generate fake CCCD (12 digits) and fake phone
        fake_cccd = "".join([str(random.randint(0, 9)) for _ in range(12)])
        fake_phone = f"0{random.choice([3,5,7,8,9])}" + "".join([str(random.randint(0, 9)) for _ in range(8)])

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace", 
                          {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace", 
                                 {"new_value": fake.email()}),
                "VN_CCCD": OperatorConfig("replace", 
                           {"new_value": fake_cccd}),
                "VN_PHONE": OperatorConfig("replace", 
                            {"new_value": fake_phone}),
            }
        elif strategy == "mask":
            # Masking: keep first and last char, mask middle with *
            operators = {
                "PERSON": OperatorConfig("mask", 
                          {"chars_to_mask": 8, "masking_char": "*", "from_end": False}),
                "EMAIL_ADDRESS": OperatorConfig("mask", 
                                 {"chars_to_mask": 10, "masking_char": "*", "from_end": False}),
                "VN_CCCD": OperatorConfig("mask", 
                           {"chars_to_mask": 10, "masking_char": "*", "from_end": False}),
                "VN_PHONE": OperatorConfig("mask", 
                            {"chars_to_mask": 6, "masking_char": "*", "from_end": False}),
            }
        elif strategy == "hash":
            # SHA-256 one-way hash
            operators = {
                "PERSON": OperatorConfig("hash", {"hash_type": "sha256"}),
                "EMAIL_ADDRESS": OperatorConfig("hash", {"hash_type": "sha256"}),
                "VN_CCCD": OperatorConfig("hash", {"hash_type": "sha256"}),
                "VN_PHONE": OperatorConfig("hash", {"hash_type": "sha256"}),
            }
        else:
            return text

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        TODO: Anonymize toàn bộ DataFrame.
        - Cột text (ho_ten, dia_chi, email): dùng anonymize_text()
        - Cột cccd, so_dien_thoai: replace trực tiếp bằng fake data
        - Cột benh, ket_qua_xet_nghiem: GIỮ NGUYÊN (cần cho model training)
        - Cột patient_id: GIỮ NGUYÊN (pseudonym đã đủ an toàn)
        """
        df_anon = df.copy()

        # Xử lý text columns với anonymize_text()
        if "ho_ten" in df_anon.columns:
            df_anon["ho_ten"] = df_anon["ho_ten"].apply(
                lambda x: self.anonymize_text(str(x), strategy="replace")
            )
        
        if "dia_chi" in df_anon.columns:
            df_anon["dia_chi"] = df_anon["dia_chi"].apply(
                lambda x: self.anonymize_text(str(x), strategy="replace")
            )
        
        if "email" in df_anon.columns:
            df_anon["email"] = df_anon["email"].apply(
                lambda x: fake.email()
            )
        
        # Replace CCCD và phone trực tiếp với fake data
        if "cccd" in df_anon.columns:
            df_anon["cccd"] = df_anon["cccd"].apply(
                lambda x: "".join([str(random.randint(0, 9)) for _ in range(12)])
            )
        
        if "so_dien_thoai" in df_anon.columns:
            df_anon["so_dien_thoai"] = df_anon["so_dien_thoai"].apply(
                lambda x: f"0{random.choice([3,5,7,8,9])}" + "".join([str(random.randint(0, 9)) for _ in range(8)])
            )
        
        if "bac_si_phu_trach" in df_anon.columns:
            df_anon["bac_si_phu_trach"] = df_anon["bac_si_phu_trach"].apply(
                lambda x: self.anonymize_text(str(x), strategy="replace")
            )
        
        # GIỮ NGUYÊN: patient_id, benh, ket_qua_xet_nghiem, ngay_sinh, ngay_kham
        # (các cột này không cần anonymize hoặc đã đủ an toàn)

        return df_anon

    def calculate_detection_rate(self, 
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        TODO: Tính % PII được detect thành công.
        Mục tiêu: > 95%

        Logic: với mỗi ô trong pii_columns,
               kiểm tra xem detect_pii() có tìm thấy ít nhất 1 entity không.
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
