"""Populate the retained Business Review PowerPoint template with Human API data.

This edits the original OOXML parts in a copy of the template so its slide masters,
layouts, geometry, text styling, tables, charts, and recurring slide chrome remain intact.
"""
from __future__ import annotations

from io import BytesIO
import posixpath
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "presentations/templates/Business_Review_Reference.pptx"
OUT = ROOT / "deliverables/HumanAPI_Business_Review.pptx"

P = "http://schemas.openxmlformats.org/presentationml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
S = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DC = "http://purl.org/dc/elements/1.1/"
NS = {"p": P, "a": A, "c": C, "r": R, "rel": REL, "s": S, "dc": DC}


def q(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


def parse_xml(data: bytes) -> ET.Element:
    for _, (prefix, uri) in ET.iterparse(BytesIO(data), events=("start-ns",)):
        ET.register_namespace(prefix, uri)
    return ET.fromstring(data)


def serialize_xml(root: ET.Element) -> bytes:
    return ET.tostring(root, encoding="UTF-8", xml_declaration=True, short_empty_elements=True)


def set_paragraph_text(paragraph: ET.Element, text: str) -> None:
    nodes = paragraph.findall(".//a:t", NS)
    if nodes:
        nodes[0].text = text
        for node in nodes[1:]:
            node.text = ""
        return
    run = ET.Element(q(A, "r"))
    ET.SubElement(run, q(A, "rPr"), {"lang": "en-US"})
    value = ET.SubElement(run, q(A, "t"))
    value.text = text
    end = paragraph.find("a:endParaRPr", NS)
    paragraph.insert(list(paragraph).index(end) if end is not None else len(paragraph), run)


def set_shape_text(slides: dict[str, bytes], slide_no: int, shape_id: str, texts: list[str]) -> None:
    name = f"ppt/slides/slide{slide_no}.xml"
    root = parse_xml(slides[name])
    shape = next((x for x in root.findall(".//p:sp", NS)
                  if x.find("p:nvSpPr/p:cNvPr", NS) is not None
                  and x.find("p:nvSpPr/p:cNvPr", NS).get("id") == shape_id), None)
    if shape is None:
        raise ValueError(f"Slide {slide_no}: shape id {shape_id} not found")
    paragraphs = [paragraph for paragraph in shape.findall("p:txBody/a:p", NS)
                  if any((node.text or "").strip() for node in paragraph.findall(".//a:t", NS))]
    if len(paragraphs) != len(texts):
        raise ValueError(f"Slide {slide_no}, shape {shape_id}: expected {len(paragraphs)} populated paragraphs, got {len(texts)}")
    for paragraph, text in zip(paragraphs, texts):
        set_paragraph_text(paragraph, text)
    slides[name] = serialize_xml(root)


def set_table(slides: dict[str, bytes], slide_no: int, rows_text: list[list[str]], header_only: bool = False) -> None:
    name = f"ppt/slides/slide{slide_no}.xml"
    root = parse_xml(slides[name])
    table = root.find(".//a:tbl", NS)
    if table is None:
        raise ValueError(f"Slide {slide_no}: table not found")
    rows = table.findall("a:tr", NS)
    targets = [rows[0]] if header_only else rows
    if len(targets) != len(rows_text):
        raise ValueError(f"Slide {slide_no}: expected {len(targets)} table rows, got {len(rows_text)}")
    for row, values in zip(targets, rows_text):
        cells = row.findall("a:tc", NS)
        if len(cells) != len(values):
            raise ValueError(f"Slide {slide_no}: expected {len(cells)} table cells, got {len(values)}")
        for cell, value in zip(cells, values):
            paragraph = cell.find("a:txBody/a:p", NS)
            if paragraph is None:
                raise ValueError(f"Slide {slide_no}: empty table cell")
            set_paragraph_text(paragraph, value)
    slides[name] = serialize_xml(root)


def set_chart_title(root: ET.Element, title: str) -> None:
    title_el = root.find("c:chart/c:title", NS)
    if title_el is None:
        raise ValueError("Chart title placeholder missing")
    tx = title_el.find("c:tx", NS)
    if tx is None:
        tx = ET.Element(q(C, "tx"))
        title_el.insert(0, tx)
    rich = tx.find("c:rich", NS)
    if rich is None:
        rich = ET.SubElement(tx, q(C, "rich"))
    for paragraph in list(rich.findall("a:p", NS)):
        rich.remove(paragraph)
    ET.SubElement(rich, q(A, "bodyPr"))
    ET.SubElement(rich, q(A, "lstStyle"))
    paragraph = ET.SubElement(rich, q(A, "p"))
    run = ET.SubElement(paragraph, q(A, "r"))
    ET.SubElement(run, q(A, "rPr"), {"lang": "en-US"})
    ET.SubElement(run, q(A, "t")).text = title
    ET.SubElement(paragraph, q(A, "endParaRPr"), {"lang": "en-US"})


def set_cache(cache: ET.Element, values: list[str]) -> None:
    count = cache.find("c:ptCount", NS)
    if count is None:
        count = ET.Element(q(C, "ptCount"))
        cache.insert(0, count)
    count.set("val", str(len(values)))
    for point in list(cache.findall("c:pt", NS)):
        cache.remove(point)
    for index, value in enumerate(values):
        point = ET.SubElement(cache, q(C, "pt"), {"idx": str(index)})
        ET.SubElement(point, q(C, "v")).text = str(value)


def update_chart(data: dict[str, bytes], chart_name: str, title: str,
                 categories: list[str], series_names: list[str], series_values: list[list[int]],
                 hide_second_series_labels: bool = False) -> None:
    root = parse_xml(data[chart_name])
    set_chart_title(root, title)
    if chart_name.endswith("chart1.xml"):
        legend_layout = root.find("c:chart/c:legend/c:layout/c:manualLayout", NS)
        if legend_layout is not None:
            x = legend_layout.find("c:x", NS)
            width = legend_layout.find("c:w", NS)
            if x is not None:
                x.set("val", "0.36")
            if width is not None:
                width.set("val", "0.62")
    series = root.findall(".//c:ser", NS)
    if len(series) != 2:
        raise ValueError(f"{chart_name}: expected two chart series")
    for index, (ser, series_name, values) in enumerate(zip(series, series_names, series_values)):
        name_cache = ser.find("c:tx/c:strRef/c:strCache", NS)
        cat_ref = ser.find("c:cat/c:strRef", NS)
        val_ref = ser.find("c:val/c:numRef", NS)
        if name_cache is None or cat_ref is None or val_ref is None:
            raise ValueError(f"{chart_name}: unexpected chart-series structure")
        name_formula = ser.find("c:tx/c:strRef/c:f", NS)
        if name_formula is not None:
            name_formula.text = f"Sheet1!${'B' if index == 0 else 'C'}$1"
        set_cache(name_cache, [series_name])
        cat_formula = cat_ref.find("c:f", NS)
        cat_cache = cat_ref.find("c:strCache", NS)
        val_formula = val_ref.find("c:f", NS)
        val_cache = val_ref.find("c:numCache", NS)
        if None in (cat_formula, cat_cache, val_formula, val_cache):
            raise ValueError(f"{chart_name}: chart cache missing")
        end_row = len(categories) + 1
        cat_formula.text = f"Sheet1!$A$2:$A${end_row}"
        val_formula.text = f"Sheet1!${'B' if index == 0 else 'C'}$2:${'B' if index == 0 else 'C'}${end_row}"
        set_cache(cat_cache, categories)
        set_cache(val_cache, [str(value) for value in values])
        if hide_second_series_labels and index == 1:
            show_value = ser.find("c:dLbls/c:showVal", NS)
            if show_value is not None:
                show_value.set("val", "0")
    data[chart_name] = serialize_xml(root)


def update_embedded_workbook(data: dict[str, bytes], filename: str, strings: list[str],
                             values: list[list[int]], table_headers: list[str]) -> None:
    with ZipFile(BytesIO(data[filename])) as source:
        book = {info.filename: source.read(info.filename) for info in source.infolist()}

    shared_name = "xl/sharedStrings.xml"
    shared = parse_xml(book[shared_name])
    entries = shared.findall("s:si", NS)
    if len(entries) != len(strings):
        raise ValueError(f"{filename}: unexpected shared-string count")
    for entry, text in zip(entries, strings):
        value = entry.find("s:t", NS)
        if value is None:
            value = ET.SubElement(entry, q(S, "t"))
        value.text = text
    book[shared_name] = serialize_xml(shared)

    sheet_name = "xl/worksheets/sheet1.xml"
    sheet = parse_xml(book[sheet_name])
    dimension = sheet.find("s:dimension", NS)
    if dimension is not None:
        dimension.set("ref", "A1:C4")
    sheet_data = sheet.find("s:sheetData", NS)
    if sheet_data is None:
        raise ValueError(f"{filename}: worksheet data missing")
    strings_by_cell = {"A1": 7, "B1": 0, "C1": 1,
                       "A2": 3, "A3": 4, "A4": 5}
    numbers = {f"{col}{row}": val for row, pair in enumerate(zip(values[0], values[1]), start=2)
               for col, val in zip(("B", "C"), pair)}
    for row in list(sheet_data.findall("s:row", NS)):
        row_num = int(row.get("r", "0"))
        if row_num > 4:
            sheet_data.remove(row)
            continue
        row.set("spans", "1:3")
        for cell in list(row.findall("s:c", NS)):
            ref = cell.get("r")
            if ref and ref.startswith("D"):
                row.remove(cell)
                continue
            if ref in strings_by_cell:
                cell.set("t", "s")
                value = cell.find("s:v", NS)
                if value is None:
                    value = ET.SubElement(cell, q(S, "v"))
                value.text = str(strings_by_cell[ref])
            elif ref in numbers:
                cell.attrib.pop("t", None)
                value = cell.find("s:v", NS)
                if value is None:
                    value = ET.SubElement(cell, q(S, "v"))
                value.text = str(numbers[ref])
    book[sheet_name] = serialize_xml(sheet)

    table_name = "xl/tables/table1.xml"
    table = parse_xml(book[table_name])
    table.set("ref", "A1:C4")
    auto_filter = table.find("s:autoFilter", NS)
    if auto_filter is not None:
        auto_filter.set("ref", "A1:C4")
    cols = table.find("s:tableColumns", NS)
    if cols is not None:
        current = cols.findall("s:tableColumn", NS)
        for col in current[3:]:
            cols.remove(col)
        cols.set("count", "3")
        for col, header in zip(cols.findall("s:tableColumn", NS), table_headers):
            col.set("name", header)
    book[table_name] = serialize_xml(table)

    workbook = parse_xml(book["xl/workbook.xml"])
    calc_pr = workbook.find("s:calcPr", NS)
    if calc_pr is not None:
        calc_pr.set("fullCalcOnLoad", "1")
        calc_pr.set("forceFullCalc", "1")
    book["xl/workbook.xml"] = serialize_xml(workbook)

    output = BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as target:
        for member, content in book.items():
            target.writestr(member, content)
    data[filename] = output.getvalue()


def set_notes(data: dict[str, bytes], slide_no: int, text: str) -> None:
    rel_name = f"ppt/slides/_rels/slide{slide_no}.xml.rels"
    if rel_name not in data:
        return
    rel_root = parse_xml(data[rel_name])
    note_rel = next((e for e in rel_root.findall("rel:Relationship", NS)
                     if e.get("Type", "").endswith("/notesSlide")), None)
    if note_rel is None:
        existing = [int(Path(name).stem.removeprefix("notesSlide"))
                    for name in data
                    if name.startswith("ppt/notesSlides/notesSlide") and name.endswith(".xml")]
        source_no = max(existing)
        new_no = source_no + 1
        source_name = f"ppt/notesSlides/notesSlide{source_no}.xml"
        note_name = f"ppt/notesSlides/notesSlide{new_no}.xml"
        note_root = parse_xml(data[source_name])

        source_rels_name = f"ppt/notesSlides/_rels/notesSlide{source_no}.xml.rels"
        note_rels = parse_xml(data[source_rels_name])
        for relation in note_rels.findall("rel:Relationship", NS):
            if relation.get("Type", "").endswith("/slide"):
                relation.set("Target", f"../slides/slide{slide_no}.xml")
        data[f"ppt/notesSlides/_rels/notesSlide{new_no}.xml.rels"] = serialize_xml(note_rels)

        slide_rel_id = max(
            (int(item.get("Id", "rId0").removeprefix("rId"))
             for item in rel_root.findall("rel:Relationship", NS)
             if item.get("Id", "").startswith("rId")),
            default=0,
        ) + 1
        note_rel = ET.SubElement(rel_root, q(REL, "Relationship"), {
            "Id": f"rId{slide_rel_id}",
            "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide",
            "Target": f"../notesSlides/notesSlide{new_no}.xml",
        })
        data[rel_name] = serialize_xml(rel_root)

        content_types_name = "[Content_Types].xml"
        content_types = parse_xml(data[content_types_name])
        part_name = f"/ppt/notesSlides/notesSlide{new_no}.xml"
        if not any(item.get("PartName") == part_name for item in content_types):
            ET.SubElement(content_types, "{http://schemas.openxmlformats.org/package/2006/content-types}Override", {
                "PartName": part_name,
                "ContentType": "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml",
            })
        data[content_types_name] = serialize_xml(content_types)
        data[note_name] = serialize_xml(note_root)
    else:
        note_name = posixpath.normpath(str(PurePosixPath("ppt/slides") / note_rel.get("Target", "")))
    root = parse_xml(data[note_name])
    body = next((shape for shape in root.findall(".//p:sp", NS)
                 if (ph := shape.find("p:nvSpPr/p:nvPr/p:ph", NS)) is not None
                 and ph.get("type") == "body"), None)
    if body is None:
        return
    paragraph = body.find("p:txBody/a:p", NS)
    if paragraph is not None:
        set_paragraph_text(paragraph, text)
    slide_number = next((shape for shape in root.findall(".//p:sp", NS)
                         if (ph := shape.find("p:nvSpPr/p:nvPr/p:ph", NS)) is not None
                         and ph.get("type") == "sldNum"), None)
    if slide_number is not None:
        number_paragraph = slide_number.find("p:txBody/a:p", NS)
        if number_paragraph is not None:
            set_paragraph_text(number_paragraph, str(slide_no))
    data[note_name] = serialize_xml(root)


def populate() -> None:
    with ZipFile(TEMPLATE) as source:
        data = {info.filename: source.read(info.filename) for info in source.infolist()}

    shapes = {
        1: {"4": ["Human API Business Review"],
            "5": ["Concept and local MVP review: current progress, evidence, value assumptions, decisions, and a proposed path to a safe pilot."],
            "6": ["Review date · 27 October 2026"],
            "10": ["Future of Work @ Presight"]},
        2: {"3": ["Human API: concept and local MVP review"], "5": ["Agenda"]},
        3: {"5": ["Project status"], "3": ["Local MVP"],
            "534": ["The local demo runs the question flow using fictional employees and files. It checks owner policy and requester access, cites evidence, routes gaps to a person, and requires approval before reusing corrections."],
            "7": ["The single most important insight"],
            "6": ["The scripted checks pass, but there is no measured employee value, live Microsoft tenant, or real-user pilot."],
            "10": ["Prove safety and value before a pilot"],
            "17": ["Leadership decision required"],
            "16": ["Sponsor a security and privacy review, then confirm each person can access only files their work account permits. Choose one willing team and use non-sensitive files."],
            "14": ["Bottom line"],
            "18": ["The base estimate is AED 700k in time value versus AED 740k in annual cost. The AED 40k gap is illustrative; time value is not cash savings."]},
        4: {"533": ["What is proven so far—and what is not"],
            "13": ["Current position"],
            "12": ["The local app demonstrates the workflow on fictional data. Microsoft connections and employee value remain unproven."],
            "14": ["Working workflow"],
            "10": ["Question records, owner rules, file checks, cited answers, escalation, and correction approval run locally."],
            "17": ["Synthetic checks"],
            "16": ["17 backend tests and 36 of 36 written search cases passed. No real employees or tenant were tested."],
            "19": ["Illustrative value"],
            "18": ["50,000 possible annual questions and AED 700k base time value are planning assumptions, not measured results."],
            "21": ["Microsoft readiness"],
            "20": ["Microsoft sign-in and file access are not connected or tested in a work account. There is no Teams app or language model."]},
        5: {"533": ["Business outcomes have not yet been measured"],
            "5": ["Current evidence is prototype-level"],
            "3": ["The local app demonstrates a question being saved, checked against owner and requester permissions, answered with a source, or routed to a person.",
                 "17 backend tests and all 36 written retrieval cases passed. These small fictional fixtures do not prove production accuracy, security, or value."],
            "28": ["Local workflow"], "27": ["Question handling and approval run with synthetic people and files."],
            "6": ["Scripted checks"], "4": ["17 backend tests and 36 search examples passed."],
            "9": ["No live outcomes"], "8": ["No employee pilot, tenant proof, or time-savings study yet."]},
        6: {"4": ["Three controls keep the workflow governed"],
            "18": ["Before any file is used"],
            "17": ["Owner consent limits dates, projects, topics, audience, and selected sources.",
                  "The requester must already be allowed to open a file. Access is checked before search and again before a saved answer is shown."],
            "6": ["Owner opt-in", "The owner chooses the scope and can pause or revoke the policy."],
            "12": ["Requester access", "Owner consent never gives another person new file access."],
            "13": ["Human fallback", "Missing or conflicting evidence goes to an approved person; reuse waits for owner approval."]},
        7: {"533": ["Strategic focus: connect before building more"],
            "3": ["Test a narrow handoff workflow on top of search tools already in use."],
            "534": ["Existing tools already search files, cite sources, and respect permissions.",
                  "Possible gap: owner-approved deadlines, source limits, human handoff, and approved reuse.",
                  "First test this workflow inside Teams or Copilot Studio."],
            "2": ["Can Microsoft tools configure this same lifecycle at lower cost?",
                 "Compare a configured workflow with the Human API prototype before funding a standalone service.",
                 "Public vendor claims change; recheck availability and licensing before a decision."]},
        8: {"533": ["The idea looks useful; its unique value is unproven"],
            "3": ["Human API should manage a controlled handoff around existing file search, not become another search engine. The next step should test whether owner permission, each person's existing file access, source citations, and human review solve a problem Microsoft tools cannot solve at lower cost."]},
        9: {"533": ["Scorecard: demo checks, not real-world results"],
            "8": ["How to read this"],
            "7": ["The demo checks its rules against fictional records.",
                 "It does not measure answer accuracy, employee value, company security, or production reliability."]},
        10: {"533": ["Illustrative annual time value and cost"],
            "18": ["Question volume"], "17": ["50,000 possible questions: 500 people × 2 per week × 50 weeks."],
            "13": ["Base-case use"], "12": ["8,400 accepted answers under illustrative adoption and resolution assumptions."],
            "15": ["Time counted"], "14": ["20 minutes of active search per accepted answer; waiting is excluded."]},
        11: {"533": ["Synthetic evaluation snapshot"],
            "3": ["36/36"], "7": ["All 36 search cases matched expected results."],
            "9": ["0"], "10": ["Scripted tests only; not a security proof."],
            "19": ["17 backend tests also passed. These small synthetic checks do not assess answer quality, tenant integration, performance, adoption, or saved time."]},
        12: {"11": ["Proposed 10-week path to a small team trial"],
            "9": ["Weeks 0–2"], "16": ["Safety review", "Review data and file controls. Pick one willing team and record a starting point."],
            "13": ["Weeks 2–6"], "17": ["Microsoft access test", "Test work-account sign-in and file access. Choose Teams or Copilot Studio."],
            "14": ["Weeks 6–10"], "18": ["Small team trial", "Run with one willing team. Measure time, trust, accepted answers, and access issues."]},
        13: {"533": ["Indicative work sequence; approvals come first"],
             "10": ["Security and privacy review"],
             "9": ["Test Microsoft work sign-in"],
             "8": ["Check each person's file access"],
             "5": ["Set up Teams or Copilot workflow"],
             "7": ["Small opt-in team trial"],
             "6": ["Measure before and during trial"]},
        14: {"4": ["Leadership decisions"],
            "5": ["Approve a security and Microsoft access review.",
                 "Choose one low-risk, willing team for a small trial.",
                 "Measure value; stop if anyone sees a file they should not."]},
    }
    for slide_no, shape_map in shapes.items():
        for shape_id, paragraphs in shape_map.items():
            set_shape_text(data, slide_no, shape_id, paragraphs)

    set_table(data, 2, [
        ["01", "Executive view and decision", "Decision"],
        ["02", "Product and roadmap status", "Progress"],
        ["03", "Evaluation and safety", "Evidence"],
        ["04", "Business case", "Assumptions"],
        ["05", "Required decisions", "Leadership"],
        ["06", "Outlook and risks", "Pilot gate"],
    ])
    set_table(data, 9, [
        ["Measure", "Current result", "What it shows", "Next proof"],
        ["Question flow", "Working locally", "Policy → answer or handoff", "Security review"],
        ["App tests", "17 passed", "Expected demo rules", "Integration tests"],
        ["Source search", "32/32 found", "Word-match cases", "Real questions"],
        ["No-answer cases", "4/4 sent to a person", "No source matched", "Reworded questions"],
        ["Access checks", "0 in tests", "Scripted cases only", "Company access review"],
        ["Live users", "Not measured", "No employee pilot", "Set baseline"],
        ["Time saved", "Not measured", "Business assumption", "Pilot time study"],
        ["Microsoft access", "Not tested", "Connection code only", "Work-account test"],
        ["Teams app", "Not built", "No Teams app", "Choose workflow host"],
    ])
    set_table(data, 13, [["Review", "Set limits", "Microsoft test", "Workflow", "Pilot"]], header_only=True)
    set_chart_title_and_data(data, 1, "AED thousands",
                             ["Low", "Base", "High"], ["Time value", "Annual cost"],
                             [[125, 700, 1611], [740, 740, 740]],
                             "ppt/embeddings/Microsoft_Excel_Worksheet.xlsx")
    set_chart_title_and_data(data, 2, "Checks by group",
                             ["Workflow", "Found source", "No answer"], ["Passed", "Failed"],
                             [[17, 32, 4], [0, 0, 0]],
                             "ppt/embeddings/Microsoft_Excel_Worksheet1.xlsx", hide_second_series_labels=True)

    notes = {
        1: "Purpose: leadership review of the Human API concept and local synthetic-data prototype. Status is presented as of 27 October 2026; project evaluation inputs were last recorded on 26 October. Sources: README.md, docs/READER_GUIDE.md, and the Idea Document.",
        2: "This agenda separates current evidence from assumptions and decisions. It is a concept-stage readout, not a quarterly operating review based on employee or customer performance data.",
        3: "Sources: PROGRESS.md and evaluations/latest_results.json (17 backend tests; 36 written search cases passed), plus the illustrative model in the Business Case. There is no live user, tenant, or productivity result.",
        4: "Sources: README.md, DEMO_GUIDE.md, PROGRESS.md, and evaluations/latest_results.json. The test set is synthetic; zero access violations refers only to the scripted cases, not a real Microsoft tenant.",
        5: "Sources: local demo scope in README.md and the Evaluation Report. Test pass counts describe expected local behavior; they do not establish answer quality, security certification, user adoption, or business impact.",
        6: "Sources: docs/SECURITY_ARCHITECTURE.md and docs/TECHNICAL_DESIGN.md. Owner consent and requester file permission are separate controls. Microsoft delegated access is planned but not tenant-tested.",
        7: "Source: docs/COMPETITIVE_ANALYSIS.md, reviewed 26 October 2026. Vendor capabilities and licensing can change; the slide frames the product distinction as a hypothesis and recommends comparison with Microsoft configuration.",
        8: "This is the product hypothesis, not a claim that Human API is unique or that current Microsoft tools cannot deliver the workflow. Validate with customer interviews and a configuration proof of concept.",
        9: "Sources: evaluations/latest_results.json and the Business Case. The table distinguishes implemented local behavior, synthetic tests, planning assumptions, and future evidence required.",
        10: "Source: HumanAPI_Business_Case.pdf. 50,000 possible questions = 500 × 2 × 50. Base case: 8,400 accepted answers × 20 active minutes × AED 250/hour = AED 700,000 estimated time value. Annual operating-cost assumption is AED 740,000. Neither value is measured cash savings.",
        11: "Sources: evaluations/latest_results.json and the Evaluation Report. Search suite: 32 expected retrievals plus 4 expected no-evidence cases, all passed. Backend: 17 tests passed. These are small synthetic checks, not semantic answer-quality, penetration, or production-security evaluations.",
        12: "This is a proposed sequence, not a committed schedule. Weeks 0–2 cover safety review and choosing a willing team; weeks 2–6 test Microsoft sign-in and file access; weeks 6–10 allow a small trial only if security review and tenant access are ready.",
        13: "Source: proposed roadmap in the Idea Document and project plan. Timing is indicative: 0–2 weeks for review, 2–6 for Microsoft proof, and 6–10 for a small pilot. It depends on security approval, tenant access, and a willing team; it is not a committed schedule.",
        14: "Decision request synthesized from the Business Case, Security Architecture, and roadmap. The pilot should proceed only after security/privacy approval and evidence that requester permissions are preserved. Stop and remediate if an unauthorized disclosure occurs.",
    }
    for slide_no, text in notes.items():
        set_notes(data, slide_no, text)

    core = parse_xml(data["docProps/core.xml"])
    title = core.find("dc:title", NS)
    if title is not None:
        title.text = "Human API Business Review — Concept and Local MVP"
    subject = core.find("dc:subject", NS)
    if subject is not None:
        subject.text = "Concept status, synthetic evaluation, illustrative business case, decisions and pilot outlook"
    data["docProps/core.xml"] = serialize_xml(core)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUT.with_suffix(".tmp.pptx")
    with ZipFile(temp, "w", ZIP_DEFLATED) as target:
        for member, content in data.items():
            target.writestr(member, content)
    temp.replace(OUT)
    print(f"Wrote template-based review: {OUT}")


def set_chart_title_and_data(data: dict[str, bytes], chart_no: int, title: str,
                             categories: list[str], series_names: list[str],
                             series_values: list[list[int]], workbook: str,
                             hide_second_series_labels: bool = False) -> None:
    chart_name = f"ppt/charts/chart{chart_no}.xml"
    update_chart(data, chart_name, title, categories, series_names, series_values,
                 hide_second_series_labels)
    strings = ["Series 1", "Series 2", "Series 3", "Category 1", "Category 2",
               "Category 3", "Category 4", " "]
    strings[0], strings[1] = series_names
    strings[3:6] = categories
    headers = ["Category", *series_names]
    update_embedded_workbook(data, workbook, strings,
                             [series_values[0], series_values[1]], headers)


if __name__ == "__main__":
    populate()
