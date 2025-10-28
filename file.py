import io
import re
import json
import base64
from datetime import datetime

import streamlit as st

# Optional: pip install pypdf
from pypdf import PdfReader

# Optional: pip install reportlab
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# ---------- Demo Data (toy rules & lists) ----------
MATRIX_VERSION = "（DEMO）令和7年5月28日施行対応版"
DEMO_MATRIX_RULES = [
    # (pattern, clause, title, rationale_tip)
    (r"\bencrypt(ion|ed|ing)?\b|\bAES\b|\bRSA\b", "5A002", "情報セキュリティ機器", "暗号機能（キーワード：AES/RSA/encryption）を検出"),
    (r"\b(servo|5-axis|cnc|CNC|axis)\b", "2B001", "工作機械（高精度）", "多軸/サーボ等の高精度ワードに合致"),
    (r"\bdrone|UAV|flight controller\b", "9A012", "無人航空機関連", "UAV/ドローン関連キーワードに一致"),
    (r"\bGaN|InP|GHz\b", "3A001", "高周波半導体/通信", "高周波・化合物半導体を示唆"),
]

SANCTIONED_DESTINATIONS_DEMO = {
    # ISO-ish or names—demo only
    "North Korea": "Comprehensively restricted (demo)",
    "DPRK": "Comprehensively restricted (demo)",
    "Russia": "Heightened measures (demo)",
    "Iran": "Heightened measures (demo)",
}

DEMO_EUL_HITS = {
    # Pretend EUL entities (demo). In real app these are versioned entries.
    "Acme Research Institute (Xland)": "EUL (demo) – due diligence required",
    "Orbital Dynamics Lab": "EUL (demo) – due diligence required",
}

def extract_pdf_text(upload):
    """Return all text from uploaded PDF (bytes)."""
    if upload is None:
        return ""
    reader = PdfReader(upload)
    chunks = []
    for page in reader.pages:
        chunks.append(page.extract_text() or "")
    return "\n".join(chunks)

def toy_rule_engine(text):
    """Very small demo classifier that looks for keywords and returns candidate clauses."""
    hits = []
    for pattern, clause, title, why in DEMO_MATRIX_RULES:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append({"clause": clause, "title": title, "why": why})
    return hits

def build_report_pdf(data_dict) -> bytes:
    """Generate a simple 判定書 + screening report PDF and return bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("該非判定書 / Screening Report（デモ）", styles['Title']))
    story.append(Spacer(1, 6))

    # Header table
    meta = [
        ["作成日", datetime.now().strftime("%Y-%m-%d %H:%M")],
        ["Matrix 版", MATRIX_VERSION],
        ["案件ID", data_dict.get("case_id", "-")],
    ]
    table = Table(meta, hAlign='LEFT', colWidths=[40*mm, 120*mm])
    table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.black),
        ('INNERGRID',(0,0),(-1,-1),0.25, colors.grey),
        ('BACKGROUND',(0,0),(-1,0), colors.whitesmoke),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE')
    ]))
    story.append(table)
    story.append(Spacer(1, 10))

    # Item section
    story.append(Paragraph("1. 物品情報（入力）", styles['Heading2']))
    item_tbl = Table([
        ["品名", data_dict.get("item_name") or "-"],
        ["HSコード(任意)", data_dict.get("hs_code") or "-"],
        ["仕様（抜粋）", data_dict.get("spec_excerpt") or "-"]
    ], colWidths=[40*mm, 120*mm])
    item_tbl.setStyle(TableStyle([('BOX',(0,0),(-1,-1),0.5,colors.black),
                                  ('INNERGRID',(0,0),(-1,-1),0.25,colors.grey)]))
    story.append(item_tbl)
    story.append(Spacer(1, 6))

    # Deal section
    story.append(Paragraph("2. 取引情報（入力）", styles['Heading2']))
    deal_tbl = Table([
        ["買主", data_dict.get("buyer") or "-"],
        ["エンドユーザー", data_dict.get("end_user") or "-"],
        ["仕向地", data_dict.get("destination") or "-"],
        ["用途", data_dict.get("end_use") or "-"],
    ], colWidths=[40*mm, 120*mm])
    deal_tbl.setStyle(TableStyle([('BOX',(0,0),(-1,-1),0.5,colors.black),
                                  ('INNERGRID',(0,0),(-1,-1),0.25,colors.grey)]))
    story.append(deal_tbl)
    story.append(Spacer(1, 6))

    # Classification results
    story.append(Paragraph("3. 該非判定（デモ）", styles['Heading2']))
    hits = data_dict.get("hits", [])
    if hits:
        rows = [["候補条項", "名称", "根拠（キーワード検出）"]]
        for h in hits:
            rows.append([h["clause"], h["title"], h["why"]])
        t = Table(rows, colWidths=[30*mm, 40*mm, 90*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0), colors.whitesmoke),
            ('BOX',(0,0),(-1,-1),0.5, colors.black),
            ('INNERGRID',(0,0),(-1,-1),0.25, colors.grey)
        ]))
        story.append(t)
    else:
        story.append(Paragraph("該当候補は検出されませんでした（デモ）", styles['BodyText']))
    story.append(Spacer(1, 6))

    # Screening
    story.append(Paragraph("4. 取引審査（デモ）", styles['Heading2']))
    scr = data_dict.get("screening", {})
    scr_rows = [
        ["EUL/制裁ヒット", "評価"],
        ["仕向地", scr.get("destination_flag") or "なし"],
        ["エンドユーザー", scr.get("end_user_flag") or "なし"],
        ["買主", scr.get("buyer_flag") or "なし"],
    ]
    scr_tbl = Table(scr_rows, colWidths=[40*mm, 120*mm])
    scr_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0), colors.whitesmoke),
        ('BOX',(0,0),(-1,-1),0.5, colors.black),
        ('INNERGRID',(0,0),(-1,-1),0.25, colors.grey)
    ]))
    story.append(scr_tbl)
    story.append(Spacer(1, 6))

    # Decision (demo)
    story.append(Paragraph("5. 総合判断（デモ）", styles['Heading2']))
    story.append(Paragraph(data_dict.get("decision_text", "—"), styles['BodyText']))
    story.append(Spacer(1, 12))

    # Disclaimers
    story.append(Paragraph(
        "【注意】本レポートはデモ用です。実際の法令順守判断や許可申請は、最新の法令・告示・通達を確認のうえ社内責任者が行ってください。",
        styles['Italic']
    ))

    doc.build(story)
    return buf.getvalue()

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Export Control Demo (JP)", page_icon="🛡️", layout="centered")

st.title("🛡️ Export Control Demo (Japan) — 該非判定・取引審査（デモ）")
st.caption("Quick mock to show the flow. Not legal advice. Not connected to METI. For demo only.")

with st.sidebar:
    st.subheader("⚙️ Options")
    use_openai = st.toggle("Use OpenAI to map fuzzy spec → terms (optional)", value=False, help="Requires API key below. Otherwise we use a pure keyword demo.")
    openai_key = st.text_input("OpenAI API Key (optional)", type="password", placeholder="sk-...")
    st.markdown("---")
    st.write("Demo rule engine looks for a few keywords (encryption, drone, GHz, CNC...).")
    st.write("You can tweak the toy rules in code (DEMO_MATRIX_RULES).")

st.header("1) Upload PDF spec (or any product brochure)")
pdf_file = st.file_uploader("Upload spec PDF", type=["pdf"])

spec_text = ""
if pdf_file:
    with st.spinner("Reading PDF..."):
        spec_text = extract_pdf_text(pdf_file)
    st.success(f"Extracted ~{len(spec_text)} characters")
    with st.expander("Preview extracted text"):
        st.write(spec_text[:4000] or "(no text found)")

st.header("2) Deal basics")
col1, col2 = st.columns(2)
with col1:
    item_name = st.text_input("Item name", placeholder="e.g., XYZ Flight Controller")
    hs_code = st.text_input("HS code (optional)", placeholder="e.g., 8526.91")
with col2:
    destination = st.text_input("Destination country", placeholder="e.g., Russia")
    end_use = st.text_input("End use (free text)", placeholder="e.g., Academic research on autonomous flight")

buyer = st.text_input("Buyer / Importer", placeholder="e.g., Orbital Dynamics Lab")
end_user = st.text_input("End user", placeholder="e.g., Acme Research Institute (Xland)")

if st.button("Run demo checks", type="primary", disabled=not (pdf_file or item_name)):
    # 1) classification (demo)
    text_for_rules = (spec_text + "\n" + item_name + "\n" + (end_use or "")).lower()
    hits = toy_rule_engine(text_for_rules)

    # 2) screening (demo EUL + sanctions)
    dest_flag = SANCTIONED_DESTINATIONS_DEMO.get(destination.strip(), None) if destination else None
    buyer_flag = DEMO_EUL_HITS.get(buyer.strip(), None) if buyer else None
    end_user_flag = DEMO_EUL_HITS.get(end_user.strip(), None) if end_user else None

    # 3) decision (demo)
    needs_license = bool(hits) or bool(dest_flag) or bool(buyer_flag) or bool(end_user_flag)
    decision_text = (
        "【DEMO】要ライセンス検討：制裁/仕向地またはEUL相当ヒット、またはリスト該当候補あり。"
        if needs_license else
        "【DEMO】現時点ではライセンス不要の可能性：ただし用途・エンドユーザーの妥当性確認が必要。"
    )

    st.subheader("Results (demo)")
    st.write("**Matrix version (demo)**:", MATRIX_VERSION)

    if hits:
        st.markdown("**Classification candidates (demo):**")
        for h in hits:
            st.write(f"- {h['clause']} / {h['title']} — _{h['why']}_")
    else:
        st.info("No classification candidates detected by demo rules.")

    st.markdown("**Screening (demo):**")
    st.write("- Destination:", dest_flag or "no hit")
    st.write("- Buyer:", buyer_flag or "no hit")
    st.write("- End user:", end_user_flag or "no hit")
    st.markdown(f"**Decision (demo):** {decision_text}")

    # Build report
    spec_excerpt = (spec_text[:600] + "…") if spec_text and len(spec_text) > 600 else (spec_text or "-")
    report_bytes = build_report_pdf({
        "case_id": f"DEMO-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "item_name": item_name,
        "hs_code": hs_code,
        "spec_excerpt": spec_excerpt,
        "buyer": buyer,
        "end_user": end_user,
        "destination": destination,
        "end_use": end_use,
        "hits": hits,
        "screening": {
            "destination_flag": dest_flag,
            "buyer_flag": buyer_flag,
            "end_user_flag": end_user_flag,
        },
        "decision_text": decision_text
    })

    st.download_button(
        label="⬇️ Download demo 判定書 + Screening PDF",
        data=report_bytes,
        file_name="demo_export_control_report.pdf",
        mime="application/pdf",
        use_container_width=True
    )

st.markdown("---")
st.caption("""
This is a CLIENT DEMO. It **does not** perform legal classification or connect to METI/MOFA systems.
For a production build, plug in: versioned Matrix tables, End User List snapshots, sanctions feeds, and proper licensing workflows.
""")
