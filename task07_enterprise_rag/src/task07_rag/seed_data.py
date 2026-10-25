from .models import DocumentChunk

# Small, deliberately fictional corpus for repeatable local demonstrations.
SEED_CHUNKS = [
    DocumentChunk(chunk_id="security-001", text="Employees must use multi-factor authentication (MFA) for all remote access to company systems. Security Operations reviews access logs every 30 days.", source_filename="security_policy.pdf", page_number=3, metadata={"department": "Security", "version": "2.1"}),
    DocumentChunk(chunk_id="security-002", text="Report suspected data exposure to the Security Operations team within one business hour. Include the affected system, time observed, and known scope. Do not include passwords in the report.", source_filename="security_policy.pdf", page_number=7, metadata={"department": "Security", "version": "2.1"}),
    DocumentChunk(chunk_id="hr-001", text="Full-time employees become eligible for annual learning reimbursement after completing 90 days of employment. Reimbursement requires manager approval and itemized receipts.", source_filename="employee_handbook.pdf", page_number=18, metadata={"department": "Human Resources", "version": "4.0"}),
    DocumentChunk(chunk_id="hr-002", text="Employees should submit learning reimbursement requests within 30 days of completing the course. Approved reimbursements are processed in the next monthly payroll cycle.", source_filename="employee_handbook.pdf", page_number=19, metadata={"department": "Human Resources", "version": "4.0"}),
    DocumentChunk(chunk_id="engineering-001", text="Production changes require a peer review, passing automated tests, and an approved change record. Emergency changes must be documented by the next business day.", source_filename="engineering_runbook.pdf", page_number=5, metadata={"department": "Engineering", "version": "1.3"}),
    DocumentChunk(chunk_id="engineering-002", text="The on-call engineer acknowledges a production incident within 10 minutes and posts status updates at least every 30 minutes until service is restored.", source_filename="engineering_runbook.pdf", page_number=11, metadata={"department": "Engineering", "version": "1.3"}),
]
