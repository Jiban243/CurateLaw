# M3.5.1 — V2 Full Agreement Diagnostic

## Capacity

- Total full agreements: 120
- V2 strong candidates: 14
- Target: 45
- Shortfall: 31
- V1-to-V2 tier changes: 73

## Screening tiers

| Tier | V1 | V2 |
|---|---:|---:|
| `strong_screening_candidate` | 83 | 14 |
| `hold_manual_review` | 36 | 88 |
| `exclude_provisional` | 1 | 18 |

## V1 to V2 transitions

| V1 tier | V2 tier | Count |
|---|---|---:|
| `strong_screening_candidate` | `hold_manual_review` | 55 |
| `hold_manual_review` | `hold_manual_review` | 33 |
| `strong_screening_candidate` | `exclude_provisional` | 15 |
| `strong_screening_candidate` | `strong_screening_candidate` | 13 |
| `hold_manual_review` | `exclude_provisional` | 2 |
| `exclude_provisional` | `exclude_provisional` | 1 |
| `hold_manual_review` | `strong_screening_candidate` | 1 |

## Most frequent V2 flags

| Category | Flag | Agreements |
|---|---|---:|
| review | `probation_notice_exception_requires_review` | 64 |
| review | `employer_only_notice_pay_option_review` | 49 |
| review | `unrequested_probation_extension` | 23 |
| legal | `historical_industrial_disputes_act_reference` | 12 |
| hard | `notice_cross_reference_points_to_other_section` | 11 |
| hard | `numeric_written_salary_disagree` | 6 |
| hard | `incomplete_full_agreement` | 1 |
| review | `execution_block_check` | 1 |
| review | `insufficient_detectable_numbered_sections` | 1 |
| review | `nonparty_accepts_appointment_possible_text_corruption` | 1 |
| review | `required_notice_days_missing` | 1 |
| review | `required_probation_months_missing` | 1 |
| review | `required_salary_missing` | 1 |
| review | `required_scheduled_weekly_hours_missing` | 1 |

## Single-blocker cases

A single-blocker case has exactly one V2 hard, review or legal flag.

| Flag | Agreements |
|---|---:|
| `review:probation_notice_exception_requires_review` | 29 |
| `review:employer_only_notice_pay_option_review` | 12 |
| `review:unrequested_probation_extension` | 5 |
| `legal:historical_industrial_disputes_act_reference` | 4 |
| `hard:notice_cross_reference_points_to_other_section` | 3 |

## Representative flagged examples

These examples are for diagnostic inspection. They have not been newly human-approved.

### review: probation_notice_exception_requires_review (64)

**GEN0005** — V2 `hold_manual_review`

**Instruction:** For a fictional Platform Engineer employed in Punjab, India, draft an illustrative employment agreement with INR 1675000 fixed annual salary, a hybrid work arrangement, 40 scheduled hours per week, 4 months of probation, and 30 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
**5. PROBATION**  
The Employee shall serve a probationary period of **four (4) months** from the date of joining. During this period, the Employer shall assess the Employee’s performance, conduct, and suitability for the role. Upon successful completion of the probation period, the Employee’s appointment shall become regular, subject to the terms of this Agreement. Either party may terminate employment during the probation period with **seven (7) days’ written notice** or pay in lieu thereof.

---

**9. CONFIDENTIALITY**  
The Employee shall not, during or after employment, disclose or use any confidential information, trade secrets, technical data, business strategies, or proprietary information of the Employer, except as required in the course of employment or as permitted by law. This obligation shall continue after termination of emp
```

**GEN0011** — V2 `exclude_provisional`

**Instruction:** For a fictional API Developer employed in Haryana, India, draft an illustrative employment agreement with INR 1925000 fixed annual salary, a hybrid work arrangement, 42 scheduled hours per week, 2 months of probation, and 30 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
The Employer reserves the right to modify the work arrangement or require full-time presence at the workplace upon reasonable notice, in accordance with business needs and applicable law.

---

Either Party may terminate the employment during the probation period by providing **seven (7) days’ written notice** or payment in lieu thereof.

---
```

### review: employer_only_notice_pay_option_review (49)

**GEN0022** — V2 `hold_manual_review`

**Instruction:** For a fictional Data Scientist employed in Delhi, India, draft an illustrative employment agreement with INR 1000000 fixed annual salary, a hybrid work arrangement, 40 scheduled hours per week, 2 months of probation, and 90 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
**5. PROBATION PERIOD**  
The Employee shall be on probation for a period of **two (2) months** from the Commencement Date. During this period, the Employer shall assess the Employee’s suitability for the role. The probation period may be extended by up to one additional month at the Employer’s discretion, with written notice to the Employee. Upon successful completion, the Employee shall be confirmed in the role.

---

**9. CONFIDENTIALITY**  
The Employee shall not, during or after employment, disclose or use any confidential information, trade secrets, or proprietary data of the Employer, except as required in the course of employment or as permitted by law. This obligation shall continue after termination of employment, to the extent permitted by law.

---
```

**GEN0002** — V2 `hold_manual_review`

**Instruction:** For a fictional IT Operations Analyst employed in Haryana, India, draft an illustrative employment agreement with INR 2175000 fixed annual salary, a remote work arrangement, 35 scheduled hours per week, 4 months of probation, and 75 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
**2. Workplace**  
The Employee’s primary place of work shall be **remote**, with performance of duties conducted from a location within Haryana, India, as agreed between the parties. The Employee shall ensure a secure, functional, and professional work environment at the remote location and remain accessible during scheduled working hours. The Employer reserves the right to require occasional in-person attendance at a designated office or facility in Haryana, with reasonable prior notice.

---

**4. Probation Period**  
The Employee shall serve a probationary period of **four (4) months**, commencing on the effective date of employment. During this period, either party may terminate the employment with **thirty (30) days’ written notice** or payment in lieu, without further liability, subject to applicable law. Upon satisfactory completi
```

### review: unrequested_probation_extension (23)

**GEN0021** — V2 `hold_manual_review`

**Instruction:** For a fictional Product Engineer employed in Rajasthan, India, draft an illustrative employment agreement with INR 1200000 fixed annual salary, a remote work arrangement, 40 scheduled hours per week, 2 months of probation, and 45 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
### 5. **PROBATION PERIOD**

The Employee shall serve a probation period of **two (2) months** from the Commencement Date. During this period, the performance and suitability of the Employee will be assessed.

The Employee shall serve a probation period of **two (2) months** from the Commencement Date. During this period, the performance and suitability of the Employee will be assessed.

The Employer may, at its discretion, confirm the Employee’s appointment upon successful completion of the probation period, extend the probation by a further period not exceeding one month, or terminate employment during probation with **fourteen (14) days’ notice** or pay in lieu thereof.
```

**GEN0022** — V2 `hold_manual_review`

**Instruction:** For a fictional Data Scientist employed in Delhi, India, draft an illustrative employment agreement with INR 1000000 fixed annual salary, a hybrid work arrangement, 40 scheduled hours per week, 2 months of probation, and 90 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
**5. PROBATION PERIOD**  
The Employee shall be on probation for a period of **two (2) months** from the Commencement Date. During this period, the Employer shall assess the Employee’s suitability for the role. The probation period may be extended by up to one additional month at the Employer’s discretion, with written notice to the Employee. Upon successful completion, the Employee shall be confirmed in the role.

**5. PROBATION PERIOD**  
The Employee shall be on probation for a period of **two (2) months** from the Commencement Date. During this period, the Employer shall assess the Employee’s suitability for the role. The probation period may be extended by up to one additional month at the Employer’s discretion, with written notice to the Employee. Upon successful completion, the Employee shall be confirmed in the role.

---
```

### legal: historical_industrial_disputes_act_reference (12)

**GEN0028** — V2 `hold_manual_review`

**Instruction:** For a fictional Release Engineer employed in Gujarat, India, draft an illustrative employment agreement with INR 2225000 fixed annual salary, a remote work arrangement, 35 scheduled hours per week, 6 months of probation, and 45 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
This Agreement shall be governed by and construed in accordance with the laws of India. Any interpretation of this Agreement shall be consistent with applicable statutes, including but not limited to the Industrial Disputes Act, 1947, the Contract Labour (Regulation and Abolition) Act, 1970 (if applicable), and other relevant central and state laws.

---
```

**GEN0002** — V2 `hold_manual_review`

**Instruction:** For a fictional IT Operations Analyst employed in Haryana, India, draft an illustrative employment agreement with INR 2175000 fixed annual salary, a remote work arrangement, 35 scheduled hours per week, 4 months of probation, and 75 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
**11. Termination**  
Either party may terminate this employment by providing **seventy-five (75) days’ written notice** to the other party. In the event of termination by the Employer without notice, the Employer shall pay the Employee an amount equivalent to seventy-five (75) days of salary in lieu of notice. Termination shall be subject to compliance with applicable labour laws, including any requirements under the Industrial Disputes Act, 1947, if applicable.

---
```

### hard: notice_cross_reference_points_to_other_section (11)

**GEN0068** — V2 `exclude_provisional`

**Instruction:** For a fictional IT Operations Analyst employed in Telangana, India, draft an illustrative employment agreement with INR 1450000 fixed annual salary, a on-site work arrangement, 40 scheduled hours per week, 5 months of probation, and 60 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
**5. PROBATION PERIOD**  
The Employee shall serve a probation period of **five (5) months** from the date of joining. During this period, the Employer shall evaluate the Employee’s performance and suitability for the role. The Employer may terminate the employment during the probation period by providing written notice in accordance with Clause 10, subject to applicable law. Upon successful completion of the probation period, the Employee’s appointment shall continue as a permanent employee, subject to the terms of this Agreement.

---

**9. CONFIDENTIALITY**  
The Employee shall not, during or after employment, disclose or use any confidential or proprietary information of the Employer, including but not limited to technical data, business processes, client information, and internal systems, except as required in the course of performin
```

**GEN0099** — V2 `exclude_provisional`

**Instruction:** For a fictional Platform Engineer employed in Kerala, India, draft an illustrative employment agreement with INR 1225000 fixed annual salary, a on-site work arrangement, 38 scheduled hours per week, 5 months of probation, and 30 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
The Employee shall serve a probation period of **five (5) months** from the date of joining. During this period, the performance of the Employee shall be reviewed by the Employer. Upon successful completion of the probation period, the Employee’s appointment shall be confirmed in writing by the Employer. The Employer reserves the right to terminate the employment during the probation period with **thirty (30) days’ notice** or pay in lieu thereof.

---

This obligation shall continue after termination of employment and shall be subject to applicable law.

---
```

### hard: numeric_written_salary_disagree (6)

**GEN0011** — V2 `exclude_provisional`

**Instruction:** For a fictional API Developer employed in Haryana, India, draft an illustrative employment agreement with INR 1925000 fixed annual salary, a hybrid work arrangement, 42 scheduled hours per week, 2 months of probation, and 30 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
### **4. SALARY**

The Employee shall receive a fixed annual salary of **INR 1,925,000 (Indian Rupees Eighteen Lakh Twenty-Five Thousand Only)**, payable in equal monthly installments in accordance with the Employer’s standard payroll practices, subject to applicable statutory deductions.

The Employee shall receive a fixed annual salary of **INR 1,925,000 (Indian Rupees Eighteen Lakh Twenty-Five Thousand Only)**, payable in equal monthly installments in accordance with the Employer’s standard payroll practices, subject to applicable statutory deductions.

This salary constitutes the full fixed compensation for the services rendered and includes no additional allowances unless separately agreed in writing.
```

**GEN0090** — V2 `exclude_provisional`

**Instruction:** For a fictional Business Systems Analyst employed in Rajasthan, India, draft an illustrative employment agreement with INR 1475000 fixed annual salary, a remote work arrangement, 40 scheduled hours per week, 2 months of probation, and 75 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
### 4. **SALARY**

The Employee shall receive a fixed annual salary of **INR 1,475,000 (Indian Rupees Fifteen Lakh Seventy-Five Thousand Only)**, payable in equal monthly installments in accordance with the Employer’s standard payroll schedule, subject to applicable statutory deductions including income tax, Provident Fund, and other deductions required by law.

The Employee shall receive a fixed annual salary of **INR 1,475,000 (Indian Rupees Fifteen Lakh Seventy-Five Thousand Only)**, payable in equal monthly installments in accordance with the Employer’s standard payroll schedule, subject to applicable statutory deductions including income tax, Provident Fund, and other deductions required by law.

---
```

### hard: incomplete_full_agreement (1)

**GEN0077** — V2 `exclude_provisional`

**Instruction:** For a fictional Application Developer employed in Maharashtra, India, draft an illustrative employment agreement with INR 1600000 fixed annual salary, a remote work arrangement, 40 scheduled hours per week, 5 months of probation, and 45 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
**1. APPOINTMENT**  
The Employer hereby appoints the Employee to the position of Application Developer, and the Employee accepts such appointment, subject to the terms and conditions set forth in this Agreement.

**1. APPOINTMENT**  
The Employer hereby appoints the Employee to the position of Application Developer, and the Employee accepts such appointment, subject to the terms and conditions set forth in this Agreement.

---
```

### review: execution_block_check (1)

**GEN0189** — V2 `hold_manual_review`

**Instruction:** For a fictional Data Scientist employed in Punjab, India, draft an illustrative employment agreement with INR 1450000 fixed annual salary, a remote work arrangement, 35 scheduled hours per week, 6 months of probation, and 30 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
**1. APPOINTMENT**

The Employer hereby appoints the Employee to the position of **Data Scientist**, and the Employee accepts such appointment, effective from the Effective Date, subject to the terms and conditions set forth in this Agreement.

The Employer hereby appoints the Employee to the position of **Data Scientist**, and the Employee accepts such appointment, effective from the Effective Date, subject to the terms and conditions set forth in this Agreement.

---
```

### review: insufficient_detectable_numbered_sections (1)

**GEN0077** — V2 `exclude_provisional`

**Instruction:** For a fictional Application Developer employed in Maharashtra, India, draft an illustrative employment agreement with INR 1600000 fixed annual salary, a remote work arrangement, 40 scheduled hours per week, 5 months of probation, and 45 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
**1. APPOINTMENT**  
The Employer hereby appoints the Employee to the position of Application Developer, and the Employee accepts such appointment, subject to the terms and conditions set forth in this Agreement.

**2. DUTIES AND RESPONSIBILITIES**  
The Employee shall perform duties and responsibilities customary to the role of an Application Developer, including but not limited to designing, developing, testing, and maintaining software applications. The Employee shall report to the designated supervisor or manager and perform such other tasks as may be assigned from time to游戏副本
```

### review: nonparty_accepts_appointment_possible_text_corruption (1)

**GEN0035** — V2 `hold_manual_review`

**Instruction:** For a fictional MLOps Specialist employed in Gujarat, India, draft an illustrative employment agreement with INR 1900000 fixed annual salary, a hybrid work arrangement, 42 scheduled hours per week, 3 months of probation, and 45 days of mutual notice. Include parties, appointment, duties, workplace, salary, probation, working time, leave, applicable statutory benefits, confidentiality, work-related IP, workplace policy, termination, disputes and signatures. Use party and date placeholders. Do not invent legal rates, extra payment amounts, or post-employment non-competes; make contractual terms subject to applicable law.

**Relevant response excerpt:**

```text
**1. APPOINTMENT**  
The Employer hereby appoints the Employee, and the Newton agrees to accept appointment, as a **MLOps Specialist**, effective from [START DATE], subject to the terms and conditions set forth in this Agreement and applicable laws.

**1. APPOINTMENT**  
The Employer hereby appoints the Employee, and the Newton agrees to accept appointment, as a **MLOps Specialist**, effective from [START DATE], subject to the terms and conditions set forth in this Agreement and applicable laws.

---
```

## Interpretation

Counts describe automatic flag occurrences. They do not establish that all flags are correct.

The next step is to inspect representative cases, fix demonstrable parser or rule errors, and separately resolve genuinely questionable contractual or legal provisions.

Original scores, datasets and human annotations were not modified.
