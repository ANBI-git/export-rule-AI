# -*- coding: utf-8 -*-
"""
🛡️ KSA 輸出管理システム - Enhanced Demo
該非判定・取引審査・ライセンス管理統合システム

Enhanced Features:
- Modern UI with status tracking
- Risk-based classification
- Interactive screening dashboard
- Advanced history with analytics
- Professional PDF reports
"""

import io
import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import random

import streamlit as st
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# =========================
# ENHANCED DEMO DATA
# =========================
MATRIX_VERSION = "令和7年5月28日施行対応版"
SYSTEM_VERSION = "v2.1.0"

# Enhanced Matrix Rules with confidence scoring
DEMO_MATRIX_RULES = [
    {
        "pattern": r"\b(encrypt(ion|ed|ing)?|AES|RSA|DES|3DES|cipher|暗号)\b",
        "clause": "5A002",
        "category": "情報セキュリティ",
        "title": "暗号機能付き情報セキュリティ機器",
        "threshold": "56ビット以上の鍵長",
        "risk_level": "HIGH",
        "confidence": 0.85
    },
    {
        "pattern": r"\b(5-axis|5軸|multi-axis|多軸|CNC|NC|servo|サーボ)\b",
        "clause": "2B001",
        "category": "工作機械",
        "title": "高精度数値制御工作機械",
        "threshold": "位置決め精度0.006mm以下",
        "risk_level": "MEDIUM",
        "confidence": 0.78
    },
    {
        "pattern": r"\b(drone|UAV|unmanned|flight controller|ドローン|無人機)\b",
        "clause": "9A012",
        "category": "航空宇宙",
        "title": "無人航空機関連装置",
        "threshold": "射程300km以上または搭載能力500kg以上",
        "risk_level": "HIGH",
        "confidence": 0.92
    },
    {
        "pattern": r"\b(GaN|InP|GaAs|SiC|GHz|高周波|MMIC)\b",
        "clause": "3A001",
        "category": "電子機器",
        "title": "高周波・化合物半導体デバイス",
        "threshold": "動作周波数3GHz以上",
        "risk_level": "MEDIUM",
        "confidence": 0.81
    },
    {
        "pattern": r"\b(laser|レーザー|LIDAR|光学|optical)\b",
        "clause": "6A005",
        "category": "センサー",
        "title": "レーザー関連装置",
        "threshold": "波長出力特性による",
        "risk_level": "MEDIUM",
        "confidence": 0.72
    },
    {
        "pattern": r"\b(carbon fiber|カーボンファイバー|composite|複合材)\b",
        "clause": "1C010",
        "category": "材料",
        "title": "繊維または糸状材料",
        "threshold": "特定の引張強度・弾性率",
        "risk_level": "LOW",
        "confidence": 0.68
    }
]

# Enhanced Sanctions/EUL Lists
SANCTIONED_DESTINATIONS = {
    "北朝鮮": {"level": "CRITICAL", "reason": "包括的禁輸措置（国連安保理決議）", "color": "#dc2626"},
    "DPRK": {"level": "CRITICAL", "reason": "包括的禁輸措置（国連安保理決議）", "color": "#dc2626"},
    "ロシア": {"level": "HIGH", "reason": "追加的措置対象（特定品目）", "color": "#ea580c"},
    "イラン": {"level": "HIGH", "reason": "追加的措置対象（WMD関連）", "color": "#ea580c"},
    "シリア": {"level": "HIGH", "reason": "武器禁輸措置", "color": "#ea580c"},
}

DEMO_EUL = {
    "Acme Research Institute": {
        "country": "Xland",
        "risk": "HIGH",
        "reason": "需要者リスト該当（WMD懸念）",
        "last_updated": "2025-03-15",
        "color": "#ea580c"
    },
    "Orbital Dynamics Lab": {
        "country": "Country Y",
        "risk": "MEDIUM",
        "reason": "需要者リスト該当（要デューデリジェンス）",
        "last_updated": "2025-02-20",
        "color": "#f59e0b"
    },
    "Global Defense Systems": {
        "country": "Various",
        "risk": "HIGH",
        "reason": "軍事転用懸念",
        "last_updated": "2025-04-01",
        "color": "#ea580c"
    }
}

# Risk assessment criteria
END_USE_RED_FLAGS = [
    "military", "軍事", "defense", "防衛", "weapon", "兵器",
    "missile", "ミサイル", "nuclear", "核", "WMD", "大量破壊兵器"
]

# =========================
# UTILITY FUNCTIONS
# =========================

def extract_pdf_text(uploaded_file) -> str:
    """Extract text from uploaded PDF"""
    if not uploaded_file:
        return ""
    try:
        reader = PdfReader(uploaded_file)
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        return text
    except Exception as e:
        st.error(f"PDF抽出エラー: {str(e)}")
        return ""


def enhanced_classify(text: str, item_name: str = "", params: str = "") -> List[Dict]:
    """Enhanced classification with confidence scoring"""
    hits = []
    combined_text = f"{text} {item_name} {params}".lower()
    
    for rule in DEMO_MATRIX_RULES:
        if re.search(rule["pattern"], combined_text, flags=re.IGNORECASE):
            # Add some randomization to confidence for demo
            confidence = min(0.99, rule["confidence"] + random.uniform(-0.05, 0.05))
            hits.append({
                "clause": rule["clause"],
                "category": rule["category"],
                "title": rule["title"],
                "threshold": rule["threshold"],
                "risk_level": rule["risk_level"],
                "confidence": confidence,
                "matched_terms": re.findall(rule["pattern"], combined_text, flags=re.IGNORECASE)[:5]
            })
    
    # Sort by confidence
    hits.sort(key=lambda x: x["confidence"], reverse=True)
    return hits


def screen_transaction(destination: str, buyer: str, end_user: str, end_use: str) -> Dict:
    """Enhanced screening with detailed risk assessment"""
    screening_result = {
        "destination": {"flag": None, "details": None},
        "buyer": {"flag": None, "details": None},
        "end_user": {"flag": None, "details": None},
        "end_use": {"flag": None, "details": None},
        "overall_risk": "LOW",
        "risk_score": 0
    }
    
    # Check destination
    dest = (destination or "").strip()
    if dest in SANCTIONED_DESTINATIONS:
        screening_result["destination"] = {
            "flag": "HIT",
            "details": SANCTIONED_DESTINATIONS[dest]
        }
        screening_result["risk_score"] += 40
    
    # Check buyer
    for entity, details in DEMO_EUL.items():
        if entity.lower() in (buyer or "").lower():
            screening_result["buyer"] = {
                "flag": "HIT",
                "details": details,
                "entity": entity
            }
            screening_result["risk_score"] += 25
            break
    
    # Check end user
    for entity, details in DEMO_EUL.items():
        if entity.lower() in (end_user or "").lower():
            screening_result["end_user"] = {
                "flag": "HIT",
                "details": details,
                "entity": entity
            }
            screening_result["risk_score"] += 30
            break
    
    # Check end use red flags
    use_text = (end_use or "").lower()
    red_flags_found = [flag for flag in END_USE_RED_FLAGS if flag in use_text]
    if red_flags_found:
        screening_result["end_use"] = {
            "flag": "WARNING",
            "details": {"red_flags": red_flags_found, "reason": "用途に懸念キーワード検出"}
        }
        screening_result["risk_score"] += 15
    
    # Calculate overall risk
    if screening_result["risk_score"] >= 50:
        screening_result["overall_risk"] = "CRITICAL"
    elif screening_result["risk_score"] >= 25:
        screening_result["overall_risk"] = "HIGH"
    elif screening_result["risk_score"] >= 10:
        screening_result["overall_risk"] = "MEDIUM"
    
    return screening_result


def generate_case_decision(classification_hits: List[Dict], screening: Dict) -> Dict:
    """Generate comprehensive case decision"""
    requires_license = bool(classification_hits) or screening["risk_score"] > 0
    
    decision = {
        "requires_license": requires_license,
        "status": "BLOCKED" if screening["overall_risk"] == "CRITICAL" else "LICENSE_REQUIRED" if requires_license else "CLEAR",
        "recommendation": "",
        "next_steps": [],
        "estimated_time": ""
    }
    
    if decision["status"] == "BLOCKED":
        decision["recommendation"] = "輸出不可：制裁対象国・団体への輸出は禁止されています。"
        decision["next_steps"] = ["本案件は承認できません", "法務部門・経産省へ相談"]
        decision["estimated_time"] = "N/A"
    elif decision["status"] == "LICENSE_REQUIRED":
        decision["recommendation"] = "許可申請必要：リスト規制品または取引審査でリスクが検出されました。"
        decision["next_steps"] = [
            "詳細な技術資料の準備",
            "エンドユース誓約書の取得",
            "経産省へ個別許可申請（NACCS経由）",
            "審査期間: 約2-3ヶ月を想定"
        ]
        decision["estimated_time"] = "2-3ヶ月"
    else:
        decision["recommendation"] = "輸出可能：現時点でリスト規制・取引審査上の問題は検出されていません。"
        decision["next_steps"] = [
            "社内承認手続きの実施",
            "出荷書類の準備",
            "該非判定書の保管（3年間）"
        ]
        decision["estimated_time"] = "即時"
    
    return decision


def build_enhanced_pdf_report(payload: Dict) -> bytes:
    """Generate enhanced PDF report with better formatting"""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="JapaneseBody",
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name="Small",
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.grey
    ))
    
    story = []
    
    # Header
    story.append(Paragraph("該非判定書・取引審査報告書", styles["Title"]))
    story.append(Spacer(1, 8))
    
    # Case info header
    header_data = [
        ["作成日時", datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")],
        ["案件ID", payload.get("case_id", "-")],
        ["Matrix版", MATRIX_VERSION],
        ["システム版", SYSTEM_VERSION],
        ["審査担当者", payload.get("reviewer", "-")]
    ]
    header_table = Table(header_data, colWidths=[45*mm, 125*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.9)),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))
    
    # Section 1: Product Info
    story.append(Paragraph("1. 物品情報", styles["Heading2"]))
    story.append(Spacer(1, 4))
    product_data = [
        ["品番・製品名", payload.get("item_name", "-")],
        ["HSコード", payload.get("hs_code", "-")],
        ["主要仕様", payload.get("key_params", "-")],
        ["仕様概要", payload.get("spec_excerpt", "-")]
    ]
    product_table = Table(product_data, colWidths=[45*mm, 125*mm])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    story.append(product_table)
    story.append(Spacer(1, 12))
    
    # Section 2: Transaction Info
    story.append(Paragraph("2. 取引情報", styles["Heading2"]))
    story.append(Spacer(1, 4))
    transaction_data = [
        ["仕向地", payload.get("destination", "-")],
        ["買主", payload.get("buyer", "-")],
        ["エンドユーザー", payload.get("end_user", "-")],
        ["用途", payload.get("end_use", "-")]
    ]
    transaction_table = Table(transaction_data, colWidths=[45*mm, 125*mm])
    transaction_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))
    story.append(transaction_table)
    story.append(Spacer(1, 12))
    
    # Section 3: Classification Results
    story.append(Paragraph("3. 該非判定結果", styles["Heading2"]))
    story.append(Spacer(1, 4))
    
    hits = payload.get("hits", [])
    if hits:
        class_data = [["条項", "区分", "品名", "しきい値", "信頼度"]]
        for h in hits:
            confidence_pct = f"{h['confidence']*100:.1f}%"
            class_data.append([
                h["clause"],
                h["category"],
                h["title"],
                h["threshold"],
                confidence_pct
            ])
        
        class_table = Table(class_data, colWidths=[22*mm, 28*mm, 55*mm, 45*mm, 20*mm])
        class_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.6)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        story.append(class_table)
    else:
        story.append(Paragraph("該当候補は検出されませんでした。", styles["JapaneseBody"]))
    
    story.append(Spacer(1, 12))
    
    # Section 4: Screening Results
    story.append(Paragraph("4. 取引審査結果", styles["Heading2"]))
    story.append(Spacer(1, 4))
    
    screening = payload.get("screening", {})
    screen_data = [["項目", "結果", "詳細"]]
    
    # Destination screening
    dest_screening = screening.get("destination", {})
    dest_flag = dest_screening.get("flag", "CLEAR")
    dest_detail = dest_screening.get("details", {}).get("reason", "ヒットなし") if dest_flag == "HIT" else "ヒットなし"
    screen_data.append(["仕向地", dest_flag, dest_detail])
    
    # Buyer screening
    buyer_screening = screening.get("buyer", {})
    buyer_flag = buyer_screening.get("flag", "CLEAR")
    buyer_detail = buyer_screening.get("details", {}).get("reason", "ヒットなし") if buyer_flag == "HIT" else "ヒットなし"
    screen_data.append(["買主", buyer_flag, buyer_detail])
    
    # End user screening
    eu_screening = screening.get("end_user", {})
    eu_flag = eu_screening.get("flag", "CLEAR")
    eu_detail = eu_screening.get("details", {}).get("reason", "ヒットなし") if eu_flag == "HIT" else "ヒットなし"
    screen_data.append(["エンドユーザー", eu_flag, eu_detail])
    
    # End use screening
    use_screening = screening.get("end_use", {})
    use_flag = use_screening.get("flag", "CLEAR")
    use_detail = use_screening.get("details", {}).get("reason", "問題なし") if use_flag == "WARNING" else "問題なし"
    screen_data.append(["用途", use_flag, use_detail])
    
    screen_table = Table(screen_data, colWidths=[40*mm, 25*mm, 105*mm])
    screen_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.4, 0.6)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(screen_table)
    story.append(Spacer(1, 8))
    
    # Risk score
    risk_score = screening.get("risk_score", 0)
    overall_risk = screening.get("overall_risk", "LOW")
    risk_color = colors.red if overall_risk == "CRITICAL" else colors.orange if overall_risk == "HIGH" else colors.green
    
    risk_data = [
        ["総合リスク評価", overall_risk],
        ["リスクスコア", f"{risk_score}/100"]
    ]
    risk_table = Table(risk_data, colWidths=[45*mm, 125*mm])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
        ('BACKGROUND', (1, 0), (1, 0), risk_color),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.whitesmoke),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold')
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 12))
    
    # Section 5: Final Decision
    story.append(Paragraph("5. 総合判断", styles["Heading2"]))
    story.append(Spacer(1, 4))
    
    decision = payload.get("decision", {})
    decision_text = decision.get("recommendation", "判定情報なし")
    story.append(Paragraph(decision_text, styles["JapaneseBody"]))
    story.append(Spacer(1, 8))
    
    # Next steps
    if decision.get("next_steps"):
        story.append(Paragraph("【次のステップ】", styles["Heading3"]))
        for step in decision["next_steps"]:
            story.append(Paragraph(f"• {step}", styles["JapaneseBody"]))
    
    story.append(Spacer(1, 12))
    
    # Footer disclaimer
    story.append(Spacer(1, 20))
    disclaimer = """
    【重要事項】
    本判定書はデモシステムにより自動生成されたものです。
    実際の輸出管理業務では、最新の法令・告示・通達に基づき、
    社内責任者による最終確認と承認が必要です。
    経済産業省が公開する最新のマトリクス表・需要者リスト・
    制裁リストを必ず確認してください。
    """
    story.append(Paragraph(disclaimer, styles["Small"]))
    
    # Build PDF
    doc.build(story)
    return buf.getvalue()


def init_session_state():
    """Initialize session state variables"""
    if "cases" not in st.session_state:
        st.session_state.cases = []
    if "current_case" not in st.session_state:
        st.session_state.current_case = {}
    if "notifications" not in st.session_state:
        st.session_state.notifications = []


# =========================
# PAGE CONFIGURATION
# =========================
st.set_page_config(
    page_title="KSA 輸出管理システム",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS
st.markdown("""
<style>
    /* Color Scheme */
    :root {
        --primary: #2563eb;
        --primary-dark: #1e40af;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --bg-dark: #0f172a;
        --bg-card: #1e293b;
        --border: #334155;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
    }
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: var(--bg-card);
        border-right: 1px solid var(--border);
    }
    
    section[data-testid="stSidebar"] > div {
        padding-top: 2rem;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }
    
    p, span, label, div {
        color: var(--text-secondary) !important;
    }
    
    /* Cards */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    
    .status-card {
        background: var(--bg-card);
        border-left: 4px solid var(--primary);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .risk-critical {
        border-left-color: var(--danger) !important;
        background: rgba(239, 68, 68, 0.1);
    }
    
    .risk-high {
        border-left-color: var(--warning) !important;
        background: rgba(245, 158, 11, 0.1);
    }
    
    .risk-medium {
        border-left-color: #3b82f6 !important;
        background: rgba(59, 130, 246, 0.1);
    }
    
    .risk-low {
        border-left-color: var(--success) !important;
        background: rgba(16, 185, 129, 0.1);
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .badge-critical {
        background: var(--danger);
        color: white;
    }
    
    .badge-high {
        background: var(--warning);
        color: white;
    }
    
    .badge-medium {
        background: #3b82f6;
        color: white;
    }
    
    .badge-low {
        background: var(--success);
        color: white;
    }
    
    .badge-clear {
        background: #64748b;
        color: white;
    }
    
    /* Progress Bar */
    .progress-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 2rem 0;
        position: relative;
    }
    
    .progress-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        position: relative;
    }
    
    .progress-circle {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: var(--bg-card);
        border: 3px solid var(--border);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: var(--text-secondary);
        z-index: 2;
    }
    
    .progress-circle.active {
        background: var(--primary);
        border-color: var(--primary);
        color: white;
    }
    
    .progress-circle.complete {
        background: var(--success);
        border-color: var(--success);
        color: white;
    }
    
    .progress-label {
        margin-top: 0.5rem;
        font-size: 0.875rem;
        text-align: center;
        color: var(--text-secondary);
    }
    
    .progress-label.active {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary), var(--primary-dark));
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > select {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
    }
    
    /* File Uploader */
    [data-testid="stFileUploader"] {
        background: var(--bg-card);
        border: 2px dashed var(--border);
        border-radius: 12px;
        padding: 2rem;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 8px 8px 0 0;
        color: var(--text-secondary);
        padding: 0.75rem 1.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary);
        color: white !important;
        border-color: var(--primary);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 8px;
    }
    
    /* Notification */
    .notification {
        background: var(--bg-card);
        border-left: 4px solid var(--primary);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(-100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    /* Confidence Bar */
    .confidence-bar {
        height: 8px;
        background: var(--border);
        border-radius: 4px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    
    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--success), var(--primary));
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
init_session_state()

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("### 🛡️ KSA 輸出管理システム")
    st.markdown(f"<small>Version {SYSTEM_VERSION}</small>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Navigation Menu
    st.markdown("#### 📋 メニュー")
    menu_items = {
        "🏠 ホーム": "home",
        "📊 ダッシュボード": "dashboard",
        "01 該非判定": "classification",
        "02 取引審査": "screening",
        "03 案件管理": "cases",
        "04 問合せ": "inquiry"
    }
    
    # Simple menu selection
    selected_menu = st.radio("", list(menu_items.keys()), label_visibility="collapsed")
    page = menu_items[selected_menu]
    
    st.markdown("---")
    
    # System Info
    st.markdown("#### ⚙️ システム情報")
    st.markdown(f"""
    <div class="metric-card">
        <small>Matrix版</small><br/>
        <strong>{MATRIX_VERSION}</strong>
    </div>
    """, unsafe_allow_html=True)
    
    # User Info
    st.markdown("#### 👤 ユーザー情報")
    reviewer_name = st.text_input("担当者名", value="田中 太郎", key="reviewer_sidebar")
    department = st.text_input("部署", value="輸出管理課", key="dept_sidebar")
    
    st.markdown("---")
    st.markdown("#### 🔔 通知")
    notification_count = len(st.session_state.notifications)
    if notification_count > 0:
        st.info(f"新着通知: {notification_count}件")
    else:
        st.success("通知はありません")

# =========================
# MAIN CONTENT
# =========================

if page == "home" or page == "dashboard":
    st.title("📊 ダッシュボード")
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3 style="margin:0; color: var(--text-primary) !important;">24</h3>
            <small>今月の案件数</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3 style="margin:0; color: var(--success) !important;">18</h3>
            <small>承認済み</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3 style="margin:0; color: var(--warning) !important;">4</h3>
            <small>審査中</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3 style="margin:0; color: var(--danger) !important;">2</h3>
            <small>要対応</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent Cases
    st.subheader("📋 最近の案件")
    
    if st.session_state.cases:
        for case in st.session_state.cases[-5:]:
            status_color = {
                "CLEAR": "low",
                "LICENSE_REQUIRED": "high",
                "BLOCKED": "critical"
            }.get(case.get("status", "CLEAR"), "medium")
            
            st.markdown(f"""
            <div class="status-card risk-{status_color}">
                <strong>案件ID: {case.get('case_id', '-')}</strong><br/>
                <small>品番: {case.get('item_name', '-')} | 仕向地: {case.get('destination', '-')}</small><br/>
                <span class="badge badge-{status_color}">{case.get('status', '-')}</span>
                <small style="float:right;">{case.get('timestamp', '-')}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("案件はまだありません。新規案件を作成してください。")
    
    st.markdown("---")
    
    # Quick Start
    st.subheader("🚀 クイックスタート")
    st.markdown("""
    1. **01 該非判定** で製品仕様を入力・アップロード
    2. **02 取引審査** で取引先・仕向地情報を入力
    3. 総合判断と該非判定書を自動生成
    4. **03 案件管理** で履歴を確認
    """)

elif page == "classification":
    st.title("01 📋 該非判定")
    
    # Progress indicator
    st.markdown("""
    <div class="progress-container">
        <div class="progress-step">
            <div class="progress-circle active">1</div>
            <div class="progress-label active">製品情報入力</div>
        </div>
        <div class="progress-step">
            <div class="progress-circle">2</div>
            <div class="progress-label">該非判定</div>
        </div>
        <div class="progress-step">
            <div class="progress-circle">3</div>
            <div class="progress-label">取引審査</div>
        </div>
        <div class="progress-step">
            <div class="progress-circle">4</div>
            <div class="progress-label">総合判断</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Main layout
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.subheader("🔧 製品情報入力")
        
        # Case ID
        case_id = st.text_input(
            "案件ID",
            value=f"KSA-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            help="自動生成されます"
        )
        
        # Product basic info
        col1, col2 = st.columns(2)
        with col1:
            item_name = st.text_input(
                "品番・製品名 *",
                placeholder="例: ART-40 Flight Controller",
                help="製品の品番または名称を入力"
            )
            hs_code = st.text_input(
                "HSコード",
                placeholder="例: 8526.91",
                help="税関コード（任意）"
            )
        
        with col2:
            key_params = st.text_input(
                "主要性能パラメータ",
                placeholder="例: AES-256, 5-axis, 3.2GHz",
                help="重要な技術仕様をカンマ区切りで入力"
            )
            product_category = st.selectbox(
                "製品カテゴリ",
                ["選択してください", "電子機器", "工作機械", "材料", "ソフトウェア", "通信機器", "その他"]
            )
        
        st.markdown("---")
        
        # PDF Upload
        st.subheader("📄 仕様書アップロード")
        uploaded_pdf = st.file_uploader(
            "製品カタログ・仕様書（PDF）",
            type=["pdf"],
            help="仕様書PDFをアップロードすると自動でテキスト抽出します"
        )
        
        spec_text = ""
        if uploaded_pdf:
            with st.spinner("PDFからテキストを抽出中..."):
                spec_text = extract_pdf_text(uploaded_pdf)
            
            st.success(f"✓ 抽出完了: 約 {len(spec_text)} 文字")
            
            with st.expander("📝 抽出テキスト（プレビュー）"):
                preview_text = spec_text[:1000] + "..." if len(spec_text) > 1000 else spec_text
                st.text_area("", value=preview_text, height=200, disabled=True)
        
        st.markdown("---")
        
        # Execute Classification
        if st.button("🔍 該非判定を実行", use_container_width=True, type="primary"):
            if not item_name:
                st.error("品番・製品名を入力してください")
            else:
                with st.spinner("該非判定を実行中..."):
                    # Simulate processing time
                    import time
                    time.sleep(1)
                    
                    # Run classification
                    hits = enhanced_classify(spec_text, item_name, key_params)
                    
                    # Save to session state
                    st.session_state.current_case = {
                        "case_id": case_id,
                        "item_name": item_name,
                        "hs_code": hs_code,
                        "key_params": key_params,
                        "product_category": product_category,
                        "spec_text": spec_text,
                        "spec_excerpt": (spec_text[:500] + "...") if len(spec_text) > 500 else spec_text,
                        "classification_hits": hits,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "reviewer": reviewer_name,
                        "status": "CLASSIFICATION_COMPLETE"
                    }
                    
                    st.success("✓ 該非判定が完了しました")
                    st.rerun()
    
    with col_right:
        st.subheader("📊 該非判定結果")
        
        if "classification_hits" in st.session_state.current_case:
            hits = st.session_state.current_case["classification_hits"]
            
            if hits:
                st.markdown(f"### {len(hits)} 件の候補が検出されました")
                
                for i, hit in enumerate(hits, 1):
                    confidence_pct = hit["confidence"] * 100
                    risk_class = hit["risk_level"].lower()
                    
                    st.markdown(f"""
                    <div class="status-card risk-{risk_class}">
                        <strong>{i}. {hit['clause']}</strong> - {hit['category']}<br/>
                        <small>{hit['title']}</small><br/>
                        <span class="badge badge-{risk_class}">{hit['risk_level']}</span>
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: {confidence_pct}%"></div>
                        </div>
                        <small>信頼度: {confidence_pct:.1f}%</small><br/>
                        <small>しきい値: {hit['threshold']}</small><br/>
                        <small>検出語: {', '.join(hit['matched_terms'][:3])}</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.info("💡 次のステップ: **02 取引審査**で取引情報を入力してください")
            else:
                st.success("✓ 該当候補は検出されませんでした")
                st.info("取引審査に進んで、仕向地・取引先情報を確認してください")
        else:
            st.info("👈 左側のフォームに製品情報を入力し、該非判定を実行してください")

elif page == "screening":
    st.title("02 🔍 取引審査")
    
    # Check if classification is complete
    if "classification_hits" not in st.session_state.current_case:
        st.warning("⚠️ 先に **01 該非判定** を実行してください")
        st.stop()
    
    # Progress indicator
    st.markdown("""
    <div class="progress-container">
        <div class="progress-step">
            <div class="progress-circle complete">✓</div>
            <div class="progress-label">製品情報入力</div>
        </div>
        <div class="progress-step">
            <div class="progress-circle complete">✓</div>
            <div class="progress-label">該非判定</div>
        </div>
        <div class="progress-step">
            <div class="progress-circle active">3</div>
            <div class="progress-label active">取引審査</div>
        </div>
        <div class="progress-step">
            <div class="progress-circle">4</div>
            <div class="progress-label">総合判断</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.subheader("📍 取引情報入力")
        
        # Transaction details
        col1, col2 = st.columns(2)
        
        with col1:
            destination = st.text_input(
                "仕向地 *",
                placeholder="例: ドイツ / ロシア / ベトナム",
                help="最終仕向地の国名を入力"
            )
            buyer = st.text_input(
                "買主",
                placeholder="例: ABC Trading Corp.",
                help="購入者・輸入者の名称"
            )
        
        with col2:
            end_user = st.text_input(
                "エンドユーザー",
                placeholder="例: XYZ Research Institute",
                help="最終需要者・使用者の名称"
            )
            transaction_type = st.selectbox(
                "取引種別",
                ["選択してください", "輸出", "技術提供", "役務取引", "その他"]
            )
        
        st.markdown("---")
        
        end_use = st.text_area(
            "用途・使用目的 *",
            placeholder="例: 産業用ロボットの制御システムとして使用\n学術研究用途\n民生品として販売",
            height=120,
            help="製品の具体的な使用目的を記載"
        )
        
        # Additional screening options
        with st.expander("🔧 詳細オプション"):
            include_historical = st.checkbox("過去の取引履歴を参照", value=True)
            strict_mode = st.checkbox("厳格モード（より厳しい審査）", value=False)
        
        st.markdown("---")
        
        # Execute Screening
        if st.button("🛡️ 取引審査を実行", use_container_width=True, type="primary"):
            if not destination or not end_use:
                st.error("必須項目（仕向地・用途）を入力してください")
            else:
                with st.spinner("取引審査を実行中..."):
                    import time
                    time.sleep(1.5)
                    
                    # Run screening
                    screening_result = screen_transaction(destination, buyer, end_user, end_use)
                    
                    # Generate decision
                    decision = generate_case_decision(
                        st.session_state.current_case["classification_hits"],
                        screening_result
                    )
                    
                    # Update session state
                    st.session_state.current_case.update({
                        "destination": destination,
                        "buyer": buyer,
                        "end_user": end_user,
                        "end_use": end_use,
                        "transaction_type": transaction_type,
                        "screening_result": screening_result,
                        "decision": decision,
                        "status": decision["status"]
                    })
                    
                    st.success("✓ 取引審査が完了しました")
                    st.rerun()
    
    with col_right:
        st.subheader("📊 審査結果")
        
        if "screening_result" in st.session_state.current_case:
            screening = st.session_state.current_case["screening_result"]
            decision = st.session_state.current_case["decision"]
            
            # Overall Risk
            risk_level = screening["overall_risk"]
            risk_score = screening["risk_score"]
            risk_class = risk_level.lower()
            
            st.markdown(f"""
            <div class="status-card risk-{risk_class}">
                <h3 style="margin:0;">総合リスク評価</h3>
                <h2 style="margin:10px 0; color: var(--text-primary) !important;">{risk_level}</h2>
                <div class="confidence-bar">
                    <div class="confidence-fill" style="width: {risk_score}%; background: var(--danger);"></div>
                </div>
                <small>リスクスコア: {risk_score}/100</small>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Detailed screening results
            st.markdown("### 詳細審査結果")
            
            # Destination
            dest_result = screening["destination"]
            if dest_result["flag"] == "HIT":
                details = dest_result["details"]
                st.markdown(f"""
                <div class="status-card risk-critical">
                    <strong>🚫 仕向地</strong><br/>
                    <span class="badge badge-critical">BLOCKED</span><br/>
                    <small>{details['reason']}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="status-card risk-low">
                    <strong>✓ 仕向地</strong><br/>
                    <span class="badge badge-clear">CLEAR</span><br/>
                    <small>問題なし</small>
                </div>
                """, unsafe_allow_html=True)
            
            # Buyer
            buyer_result = screening["buyer"]
            if buyer_result["flag"] == "HIT":
                details = buyer_result["details"]
                risk_class_buyer = "critical" if details["risk"] == "HIGH" else "high"
                st.markdown(f"""
                <div class="status-card risk-{risk_class_buyer}">
                    <strong>⚠️ 買主</strong><br/>
                    <span class="badge badge-{risk_class_buyer}">HIT</span><br/>
                    <small>{buyer_result['entity']}</small><br/>
                    <small>{details['reason']}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="status-card risk-low">
                    <strong>✓ 買主</strong><br/>
                    <span class="badge badge-clear">CLEAR</span><br/>
                    <small>問題なし</small>
                </div>
                """, unsafe_allow_html=True)
            
            # End User
            eu_result = screening["end_user"]
            if eu_result["flag"] == "HIT":
                details = eu_result["details"]
                risk_class_eu = "critical" if details["risk"] == "HIGH" else "high"
                st.markdown(f"""
                <div class="status-card risk-{risk_class_eu}">
                    <strong>⚠️ エンドユーザー</strong><br/>
                    <span class="badge badge-{risk_class_eu}">HIT</span><br/>
                    <small>{eu_result['entity']}</small><br/>
                    <small>{details['reason']}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="status-card risk-low">
                    <strong>✓ エンドユーザー</strong><br/>
                    <span class="badge badge-clear">CLEAR</span><br/>
                    <small>問題なし</small>
                </div>
                """, unsafe_allow_html=True)
            
            # End Use
            use_result = screening["end_use"]
            if use_result["flag"] == "WARNING":
                details = use_result["details"]
                st.markdown(f"""
                <div class="status-card risk-high">
                    <strong>⚠️ 用途</strong><br/>
                    <span class="badge badge-high">WARNING</span><br/>
                    <small>懸念キーワード: {', '.join(details['red_flags'][:3])}</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="status-card risk-low">
                    <strong>✓ 用途</strong><br/>
                    <span class="badge badge-clear">CLEAR</span><br/>
                    <small>問題なし</small>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Final Decision
            st.markdown("### 📋 総合判断")
            
            status_color_map = {
                "BLOCKED": "critical",
                "LICENSE_REQUIRED": "high",
                "CLEAR": "low"
            }
            status_class = status_color_map.get(decision["status"], "medium")
            
            st.markdown(f"""
            <div class="status-card risk-{status_class}">
                <h4 style="margin:0 0 10px 0; color: var(--text-primary) !important;">
                    {decision['status'].replace('_', ' ')}
                </h4>
                <p style="color: var(--text-primary) !important;">{decision['recommendation']}</p>
                <small>想定処理時間: {decision['estimated_time']}</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Next Steps
            if decision["next_steps"]:
                st.markdown("### 📝 次のステップ")
                for step in decision["next_steps"]:
                    st.markdown(f"• {step}")
            
            st.markdown("---")
            
            # Generate Report
            if st.button("📄 該非判定書・審査報告書を生成", use_container_width=True):
                with st.spinner("PDF生成中..."):
                    pdf_bytes = build_enhanced_pdf_report(st.session_state.current_case)
                    
                    st.download_button(
                        label="💾 PDFをダウンロード",
                        data=pdf_bytes,
                        file_name=f"{st.session_state.current_case['case_id']}_report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                    # Save to cases history
                    st.session_state.cases.append(st.session_state.current_case.copy())
                    
                    st.success("✓ PDFが生成されました。案件を保存しました。")
        else:
            st.info("👈 左側のフォームに取引情報を入力し、審査を実行してください")

elif page == "cases":
    st.title("03 📁 案件管理")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_status = st.selectbox(
            "ステータス",
            ["すべて", "CLEAR", "LICENSE_REQUIRED", "BLOCKED"]
        )
    with col2:
        filter_date = st.date_input("日付範囲", [])
    with col3:
        search_term = st.text_input("🔍 検索", placeholder="品番、仕向地で検索")
    
    st.markdown("---")
    
    # Display cases
    if st.session_state.cases:
        st.subheader(f"📋 案件一覧 ({len(st.session_state.cases)}件)")
        
        # Filter cases
        filtered_cases = st.session_state.cases
        if filter_status != "すべて":
            filtered_cases = [c for c in filtered_cases if c.get("status") == filter_status]
        if search_term:
            filtered_cases = [
                c for c in filtered_cases
                if search_term.lower() in c.get("item_name", "").lower()
                or search_term.lower() in c.get("destination", "").lower()
            ]
        
        # Display filtered cases
        for case in reversed(filtered_cases):
            status_class = {
                "CLEAR": "low",
                "LICENSE_REQUIRED": "high",
                "BLOCKED": "critical"
            }.get(case.get("status", "CLEAR"), "medium")
            
            with st.expander(f"**{case['case_id']}** - {case['item_name']} → {case.get('destination', '-')}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"""
                    **案件ID**: {case['case_id']}<br/>
                    **品番**: {case['item_name']}<br/>
                    **仕向地**: {case.get('destination', '-')}<br/>
                    **買主**: {case.get('buyer', '-')}<br/>
                    **エンドユーザー**: {case.get('end_user', '-')}<br/>
                    **作成日時**: {case['timestamp']}<br/>
                    **担当者**: {case.get('reviewer', '-')}
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="status-card risk-{status_class}">
                        <strong>ステータス</strong><br/>
                        <span class="badge badge-{status_class}">{case['status']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Download report button
                    if st.button("📄 レポート再生成", key=f"report_{case['case_id']}"):
                        pdf_bytes = build_enhanced_pdf_report(case)
                        st.download_button(
                            "💾 PDFダウンロード",
                            data=pdf_bytes,
                            file_name=f"{case['case_id']}_report.pdf",
                            mime="application/pdf",
                            key=f"download_{case['case_id']}"
                        )
    else:
        st.info("案件はまだありません。**01 該非判定**から新規案件を作成してください。")

elif page == "inquiry":
    st.title("04 📧 問合せ")
    
    st.markdown("""
    システムに関するご質問、導入・PoC・追加機能のご相談はこちらからお問い合わせください。
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        contact_name = st.text_input("お名前 *")
        contact_email = st.text_input("メールアドレス *")
    
    with col2:
        company = st.text_input("会社名")
        phone = st.text_input("電話番号")
    
    inquiry_type = st.selectbox(
        "問合せ種別 *",
        ["選択してください", "システム操作について", "導入・見積について", "技術的な質問", "その他"]
    )
    
    message = st.text_area(
        "お問い合わせ内容 *",
        placeholder="詳細をご記入ください",
        height=150
    )
    
    if st.button("📩 送信", use_container_width=True, type="primary"):
        if not contact_name or not contact_email or not message or inquiry_type == "選択してください":
            st.error("必須項目（*）を入力してください")
        else:
            st.success("✓ お問い合わせを受け付けました。担当者より2営業日以内にご連絡いたします。")
            
            # Add notification
            st.session_state.notifications.append({
                "type": "inquiry",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "message": "新しいお問い合わせを送信しました"
            })

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: var(--text-secondary); font-size: 0.875rem;">
    <p>KSA 輸出管理システム Enhanced Demo v2.1.0</p>
    <p>※ 本システムはデモ版です。実際の輸出管理業務では、最新の法令・告示・通達に基づき、社内責任者による最終確認が必要です。</p>
</div>
""", unsafe_allow_html=True)
