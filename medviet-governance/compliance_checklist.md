# NĐ13/2023 Compliance Checklist — MedViet AI Platform

## A. Data Localization
- [ ] Tất cả patient data lưu trên servers đặt tại Việt Nam
- [ ] Backup cũng phải ở trong lãnh thổ VN
- [ ] Log việc transfer data ra ngoài nếu có

## B. Explicit Consent
- [ ] Thu thập consent trước khi dùng data cho AI training
- [ ] Có mechanism để user rút consent (Right to Erasure)
- [ ] Lưu consent record với timestamp

## C. Breach Notification (72h)
- [ ] Có incident response plan
- [ ] Alert tự động khi phát hiện breach
- [ ] Quy trình báo cáo đến cơ quan có thẩm quyền trong 72h

## D. DPO Appointment
- [ ] Đã bổ nhiệm Data Protection Officer
- [ ] DPO có thể liên hệ tại: **dpo@medviet.vn** *(Phòng Pháp chế & An toàn thông tin)*

## E. Technical Controls (mapping từ requirements)
| NĐ13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline (Presidio) | ✅ Done | AI Team |
| Access control | RBAC (Casbin) + ABAC (OPA) | ✅ Done | Platform Team |
| Encryption | AES-256 at rest, TLS 1.3 in transit | 🚧 In Progress | Infra Team |
| Audit logging | Centralized Logging (FastAPI Middleware + Loki/CloudTrail) | ⬜ Todo | Platform Team |
| Breach detection | Anomaly monitoring (Prometheus + Alertmanager) | ⬜ Todo | Security Team |

## F. Giải pháp kỹ thuật cho các hạng mục Todo

### 1. Audit logging (Tracking truy cập & thay đổi dữ liệu)
**Owner:** Platform Team
**Technical Solution:**
* **Application Level:** Viết một Audit Middleware trong FastAPI để tự động ghi log mọi request chạm vào các endpoint chứa dữ liệu nhạy cảm (như `/api/patients/{id}`). Log phải chứa format JSON chuẩn bao gồm: `timestamp`, `user_id`, `action` (READ/UPDATE/DELETE), `resource_id`, và `IP address`. Sau đó đẩy tập trung về **Grafana Loki** để lưu trữ và truy vấn.
* **Infrastructure Level:** Bật AWS CloudTrail (nếu dùng AWS) hoặc Audit log của Database/Vault để ghi nhận mọi hành vi gọi API giải mã (KMS/DEK) hoặc truy cập trực tiếp vào DB, đảm bảo không ai có thể âm thầm xuất dữ liệu mà không bị ghi lại.

### 2. Breach detection (Phát hiện rò rỉ dữ liệu)
**Owner:** Security Team
**Technical Solution:**
* **Metrics & Monitoring:** Sử dụng **Prometheus** để thu thập metrics từ hệ thống. Thiết lập các Alert Rules (luật cảnh báo) dựa trên hành vi bất thường (Anomaly).
* **Alert Scenarios:** * Cảnh báo nếu một user/IP tải xuống quá 50 hồ sơ bệnh án trong vòng 1 phút (Spike in data access).
  * Cảnh báo nếu có lượng lớn request giải mã DEK (Data Encryption Key) bị thất bại liên tục (Dấu hiệu brute-force hệ thống Vault).
* **Notification Routing:** Sử dụng **Prometheus Alertmanager** để đẩy thông báo khẩn cấp (P0 alert) thẳng vào kênh Slack của đội Security và gửi Email/SMS, đảm bảo đội phản ứng có thể xử lý và báo cáo sự cố trong vòng "SLA 72 giờ vàng" theo yêu cầu của NĐ13.