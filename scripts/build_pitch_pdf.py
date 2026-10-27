"""Render the deck content as a 16:9 PDF when Keynote export is unavailable."""
from __future__ import annotations

from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables/HumanAPI_Pitch_Deck.pdf"
W, H = 960, 540
C = {"forest": "17352F", "deep": "112B27", "green": "2F8069", "mint": "BFE7D6",
     "pale": "E8F1EC", "paper": "F4F6F3", "white": "FFFFFF", "ink": "24342F",
     "muted": "63756D", "line": "D7E1DB", "coral": "E87C65", "peach": "FFF0E9",
     "blue": "5278B8", "lavender": "EEEAF9", "gold": "D1A04A"}


def col(name):
    return colors.HexColor("#" + C.get(name, name))


def ptext(c, txt, x, top, width, *args, size=None, color=None, leading=None, bold=None, align=None):
    # Accept both compact calls and the old (height, size, color, ...) form.
    if len(args) >= 3 and isinstance(args[1], (int, float)) and isinstance(args[2], str):
        _height, parsed_size, parsed_color, *tail = args
        parsed_leading = tail[0] if len(tail) > 0 and isinstance(tail[0], (int, float)) else None
        parsed_bold = tail[1] if len(tail) > 1 and isinstance(tail[1], bool) else None
        parsed_align = tail[2] if len(tail) > 2 and isinstance(tail[2], (int, float)) else None
    else:
        parsed_size = args[0] if len(args) > 0 else None
        parsed_color = args[1] if len(args) > 1 and isinstance(args[1], str) else None
        parsed_leading = args[2] if len(args) > 2 and isinstance(args[2], (int, float)) else None
        parsed_bold = args[3] if len(args) > 3 and isinstance(args[3], bool) else None
        parsed_align = args[4] if len(args) > 4 and isinstance(args[4], (int, float)) else None
    size = size if size is not None else (parsed_size if parsed_size is not None else 12)
    color = color if color is not None else (parsed_color if parsed_color is not None else "ink")
    leading = leading if leading is not None else parsed_leading
    bold = bold if bold is not None else (parsed_bold if parsed_bold is not None else False)
    align = align if align is not None else (parsed_align if parsed_align is not None else 0)
    face = "Helvetica-Bold" if bold else "Helvetica"
    style = ParagraphStyle("p", fontName=face, fontSize=size, leading=leading or size * 1.28,
                           textColor=col(color), alignment=align, spaceAfter=0, spaceBefore=0)
    p = Paragraph(escape(txt).replace("\n", "<br/>"), style)
    _, height = p.wrap(width, H)
    p.drawOn(c, x, H - top - height)
    return height


def rect(c, x, top, width, height, fill="white", radius=12, stroke=None):
    c.setFillColor(col(fill))
    c.setStrokeColor(col(stroke or fill))
    c.setLineWidth(0.8)
    c.roundRect(x, H - top - height, width, height, radius, fill=1, stroke=1 if stroke else 0)


def line(c, x1, top1, x2, top2, color="green", width=1.4, dash=None):
    c.setStrokeColor(col(color)); c.setLineWidth(width)
    if dash: c.setDash(dash)
    c.line(x1, H - top1, x2, H - top2)
    c.setDash()


def base(c, n, kicker, heading, sub=None, dark=False):
    bg = "deep" if dark else "paper"
    c.setFillColor(col(bg)); c.rect(0, 0, W, H, fill=1, stroke=0)
    if dark:
        c.setFillColor(col("forest")); c.circle(856, H - 105, 145, fill=1, stroke=0)
    if kicker:
        ptext(c, kicker.upper(), 44, 29, 860, 8.5, "mint" if dark else "green", bold=True)
        ptext(c, heading, 44, 57, 870, 25, "white" if dark else "forest", leading=29, bold=True)
        if sub: ptext(c, sub, 45, 96, 850, 11.3, "mint" if dark else "muted", leading=15)
    c.setStrokeColor(col("line") if not dark else col("forest")); c.setLineWidth(.7)
    c.line(40, 24, W - 40, 24)
    ptext(c, "HUMAN API  /  EUREKA INNOVATION HACKATHON", 42, 514, 520, 7.2, "muted" if not dark else "muted", bold=True)
    ptext(c, "CONCEPT FORMULATED  ·  26 OCT 2026", 680, 514, 235, 7.2, "muted", align=2)
    ptext(c, f"{n:02}", 920, 514, 20, 7.2, "muted", align=2)


def pill(c, label, x, top, width, fill="pale", fg="green"):
    rect(c, x, top, width, 25, fill, 12)
    ptext(c, label, x + 7, top + 6, width - 14, 7.7, fg, bold=True, align=1)


def card(c, x, top, width, height, heading, body, accent="green", fill="white", body_size=10.3):
    rect(c, x, top, width, height, fill, 12, "line")
    c.setFillColor(col(accent)); c.roundRect(x, H-top-height, 5, height, 2, fill=1, stroke=0)
    ptext(c, heading, x+17, top+15, width-32, 12.5, "forest", leading=15, bold=True)
    ptext(c, body, x+17, top+45, width-32, body_size, "muted", leading=body_size*1.3)


def footer_source(c, text="Background and sources: see the companion PowerPoint speaker notes."):
    ptext(c, text, 45, 489, 850, 7.0, "muted")


def slide1(c):
    base(c, 1, None, None, dark=True)
    pill(c, "FUTURE OF WORK @ PRESIGHT", 58, 54, 205, "forest", "mint")
    ptext(c, "Human API", 58, 135, 640, 70, 52, "white", 58, True)
    ptext(c, "Help answer work questions\nwhen the expert is away", 60, 227, 660, 66, 22, "mint", 27)
    ptext(c, "A cited answer when the evidence is clear. A person when it is not.", 60, 333, 660, 44, 14, "white", 19)
    ptext(c, "EUREKA INNOVATION HACKATHON  ·  EARLY CONCEPT", 60, 453, 670, 20, 8.5, "mint", bold=True)
    ptext(c, "LOCAL DEMO · FICTIONAL DATA", 696, 453, 220, 20, 8, "mint", align=2, bold=True)


def slide2(c):
    base(c, 2, "01 / The problem", "Work can stop at the person who knows", "A question needs context, but the right person or file is hard to find.")
    items = [("A decision is needed", "An engineer needs to understand a service change."),
             ("The expert is away", "The person who remembers the reason is unavailable."),
             ("Files are scattered", "A decision note or operating guide may hold the answer."),
             ("Work waits or interrupts", "Someone waits or interrupts another expert.")]
    for i, (head, body) in enumerate(items):
        x = 46 + i * 222
        accent = "coral" if i == 3 else "green"
        rect(c, x, 184, 197, 151, "peach" if i == 3 else "white", 12, "line")
        c.setFillColor(col(accent)); c.roundRect(x, H-184-151, 5, 151, 2, fill=1, stroke=0)
        ptext(c, f"0{i+1}", x+16, 198, 35, 23, 16, accent, bold=True)
        ptext(c, head, x+16, 228, 165, 25, 10.6, "forest", bold=True)
        ptext(c, body, x+16, 260, 165, 45, 9.2, "muted", leading=12)
        if i < 3: line(c, x+201, 257, x+218, 257)
    rect(c, 47, 370, 866, 55, "pale")
    ptext(c, "A problem to test—not a Presight measurement", 65, 386, 425, 22, 12, "forest", bold=True)
    ptext(c, "Measure search time. Do not count waiting as saved work.", 492, 388, 398, 22, 9.6, "muted", align=2)
    footer_source(c)


def slide3(c):
    base(c, 3, "02 / A realistic example", "Why did the service setting change?", "Alice asks Bob about a fictional Project Alpha change.")
    rect(c, 50, 166, 298, 258, "white", 13, "line"); pill(c, "ASKED BY ALICE", 69, 184, 118, "lavender", "blue")
    ptext(c, "Why did the timeout change from 90 to 120 seconds? Is 120 seconds still needed?", 70, 230, 258, 105, 17, "forest", 22, True)
    ptext(c, "Directed to Bob · DevOps / project owner\nSynthetic out-of-office status", 70, 360, 258, 43, 9.5, "muted", 13)
    line(c, 369, 291, 432, 291, "green", 2)
    rect(c, 450, 166, 456, 258, "pale")
    pill(c, "SOFTWARE ANSWER · PARTIAL", 475, 184, 195, "mint", "green")
    ptext(c, "The decision note says the timeout rose because setup sometimes took longer than 90 seconds. The change was approved for release 5.2. The note does not say whether 120 seconds is still needed today.", 475, 229, 395, 131, 13, "forest", 18)
    ptext(c, "SOURCE  ADR-024 · written decision · version 1.0", 475, 373, 395, 15, 8.4, "green", bold=True)
    ptext(c, "This is not a reply written by Bob.", 475, 397, 395, 15, 8, "muted")
    footer_source(c)


def slide4(c):
    base(c, 4, "03 / Business impact", "What time might the idea save?", "A planning example—not a measured Presight figure.")
    ptext(c, "50,000", 58, 172, 255, 63, 42, "forest", 49, True)
    ptext(c, "possible work questions each year", 60, 245, 280, 23, 10, "muted")
    ptext(c, "500 employees × 2 questions/week × 50 weeks", 60, 294, 340, 31, 11, "green", bold=True)
    card(c, 52, 365, 260, 102, "Count search time", "Time people spend finding and checking an answer.", "green", "white", 9.2)
    card(c, 348, 365, 260, 102, "Do not count waiting", "Time spent waiting is not automatically saved work.", "coral", "peach", 9.2)
    card(c, 644, 365, 260, 102, "Measure real use", "Count answers people accept and time a pilot can verify.", "blue", "white", 9.2)
    ptext(c, "EXAMPLE ASSUMPTIONS · NOT MEASURED BENEFIT", 58, 472, 300, 11, 7.5, "blue", bold=True)
    footer_source(c)


def slide5(c):
    base(c, 5, "04 / The solution", "Owner consent does not give file access", "Two separate checks protect the person asking and the person sharing knowledge.")
    card(c, 52, 188, 265, 164, "The owner agrees", "Choose dates, project, topic, coworkers, files and backup. Pause or stop any time.")
    card(c, 347, 188, 265, 164, "The asker has access", "Use only files the requester is already allowed to open.", "blue")
    card(c, 642, 188, 265, 164, "Answer or get help", "Show the source and limits. Deny restricted requests. Ask a human when evidence is weak.", "coral")
    line(c, 319, 269, 342, 269); line(c, 614, 269, 637, 269)
    rect(c, 52, 386, 855, 62, "forest")
    ptext(c, "Every answer shows", 74, 405, 240, 22, 13.5, "white", bold=True)
    ptext(c, "Who wrote it / source / what is unknown / who can help next", 325, 407, 550, 18, 10.5, "mint", align=2)
    footer_source(c)


def slide6(c):
    base(c, 6, "05 / How it works", "One question, five clear steps", "The app records what happened and checks file access before searching.")
    labels = [("01", "Save the\nquestion"), ("02", "Check owner's\nlimits"), ("03", "Check asker's\nfile access"), ("04", "Search\napproved files"), ("05", "Answer or\nask a person")]
    for i, (num, label) in enumerate(labels):
        x = 62 + i*180
        c.setFillColor(col("coral" if i == 4 else "green")); c.circle(x+42, H-229, 24, fill=1, stroke=0)
        ptext(c, num, x+21, 221, 42, 18, 11.5, "white", bold=True, align=1)
        ptext(c, label, x-2, 274, 88, 38, 10.5, "forest", 13, True, 1)
        if i < 4: line(c, x+71, 229, x+171, 229)
    card(c, 57, 355, 405, 84, "A source supports the answer", "Show the file, version and known limits", "green", "white", 9)
    card(c, 498, 355, 405, 84, "No proof, restricted or conflict", "Give a safe denial or ask an approved person", "coral", "peach", 9)
    footer_source(c)


def slide7(c):
    base(c, 7, "06 / Owner's choice", "What Bob has agreed to", "The owner can pause or stop the helper at any time.")
    rect(c, 52, 170, 535, 266, "white", 13, "line")
    config = [("DATES", "20 Oct – 02 Nov"), ("PROJECT", "Project Alpha"), ("QUESTION TOPICS", "Deployment · timeout"),
              ("WHO MAY ASK", "Approved project colleagues"), ("FILES TO CHECK", "Selected decision notes / guides"), ("BACKUP PERSON", "Carla Mendez")]
    for i, (k, v) in enumerate(config):
        x = 75 + (i%2)*250; top = 196 + (i//2)*74
        ptext(c, k, x, top, 200, 11, 7.5, "muted", bold=True)
        ptext(c, v, x, top+22, 225, 21, 10.8, "forest", bold=True)
    rect(c, 615, 170, 291, 266, "forest")
    pill(c, "OWNER CONTROL", 640, 192, 122, "forest", "mint")
    ptext(c, "Pause or stop", 640, 239, 240, 30, 18, "white", bold=True)
    ptext(c, "A manager reviews changes. Being Busy or away never counts as permission.", 640, 286, 228, 67, 10.7, "white", 14)
    ptext(c, "Every change is recorded.", 640, 394, 225, 22, 8.5, "mint", bold=True)
    footer_source(c)


def slide8(c):
    base(c, 8, "07 / Possible Microsoft connection", "Where a Microsoft connection could fit", "These connections are not part of the tested local demo.")
    data = [("Work sign-in", "Check who is signed in with a Microsoft work account. Early code only; needs tenant testing.", "NOT CONNECTED", "blue", "lavender"),
            ("SharePoint files", "Search and open files as Alice, using Alice's existing access. Adapter not tenant-tested.", "NOT TENANT TESTED", "green", "pale"),
            ("Out-of-office status", "Possible future check of owner's status and dates only. No inbox or message text.", "EARLY ADAPTER", "gold", "peach"),
            ("Teams", "No bot yet. A future app needs registration, a secure web address and tenant approval.", "FUTURE WORK", "coral", "peach")]
    for i, (h,b,status,accent,pfill) in enumerate(data):
        x=49+i*219
        card(c,x,183,199,185,h,b,accent,"white",9)
        pill(c,status,x+16,326,145,pfill,accent)
    rect(c,52,393,855,50,"forest")
    ptext(c,"Future file search must use the requester's own Microsoft permissions.",67,410,825,17,11,"white",bold=True,align=1)
    footer_source(c)


def slide9(c):
    base(c, 9, "08 / Safety", "The requester keeps control of file access", "The owner's permission never unlocks files for another person.")
    nodes=[("Who is asking?","Work identity · project\nquestion · deadline"),("What did owner allow?","Dates · topic\npeople · files"),("Can asker open file?","Project access\nfile permissions"),("Does source answer?","Approved file\nmissing · conflict"),("What happens next?","Show source\ndeny · ask human")]
    for i,(h,b) in enumerate(nodes):
        x=48+i*180; rect(c,x,195,159,112,"pale" if i in (1,3) else "white",10,"line")
        ptext(c,h,x+10,215,139,16,10.4,"forest",bold=True,align=1)
        ptext(c,b,x+10,245,139,35,8.4,"muted",11,False,1)
        if i<4: line(c,x+162,251,x+176,251)
    rect(c,50,340,389,72,"peach")
    ptext(c,"If access is denied",70,354,120,16,11,"coral",bold=True)
    ptext(c,"Give no file name, content or clue that it exists.",195,354,220,42,8.7,"ink",11)
    rect(c,458,340,449,72,"forest")
    ptext(c,"Audit trail",478,354,110,16,11,"mint",bold=True)
    ptext(c,"Record the owner's choice, file check, source and result.",591,354,290,42,8.7,"white",11)
    ptext(c,"Not built for production yet: encrypted storage, deletion controls, real file labels, multi-server safety or independent review.",60,444,835,28,8.7,"muted",12,True,1)
    footer_source(c)


def slide10(c):
    base(c, 10, "09 / Working demo", "A real local app with fictional data", "Question records and approval steps work; all people and files are examples.")
    img=ImageReader(str(ROOT/"deliverables/HumanAPI_App_Screenshot.png"))
    c.drawImage(img,45,H-139-335,width=515,height=335,preserveAspectRatio=True,anchor='c',mask='auto')
    card(c,585,160,322,78,"The question is saved","See its status, response deadline and history.","green","white",8.7)
    card(c,585,258,322,78,"The answer shows its source","The decision note explains the change, not whether it is still needed.","blue","white",8.7)
    card(c,585,356,322,78,"A person handles gaps","Unclear answers go to a human; reuse needs approval.","coral","white",8.7)
    pill(c,"FICTIONAL DATA · NO LIVE MICROSOFT OR AI MODEL",585,450,320,"pale","green")
    footer_source(c)


def slide11(c):
    base(c, 11, "10 / AI and human roles", "AI may explain evidence; people and rules keep control", "The demo uses no language model. A future AI must never decide who may see a file.")
    blocks=[("SOFTWARE RULES","Verify identity\nCheck owner approval\nCheck file access\nHonor revocation","pale","green"),
            ("POSSIBLE FUTURE AI","Summarize allowed files\nDraft a cited answer\nSay what is unknown","white","blue"),
            ("PEOPLE DECIDE","Resolve uncertainty\nApprove corrections\nChange or stop policy","peach","coral")]
    for i,(h,b,fill,accent) in enumerate(blocks):
        x=51+i*295; rect(c,x,183,260,244,fill,12,"line")
        ptext(c,h,x+19,206,222,15,8.5,accent,bold=True)
        ptext(c,b,x+19,245,219,130,13, "forest", 20, True)
    line(c,315,304,337,304);line(c,610,304,632,304)
    ptext(c,"The current demo follows a small set of steps. Add more AI only if a pilot shows it helps.",70,449,820,30,10,"muted",14,False,1)
    footer_source(c)


def slide12(c):
    base(c, 12, "11 / What already exists", "Search is common. The workflow is the question.", "Microsoft and other tools already find files, show sources and respect file permissions.")
    card(c, 52, 188, 265, 164, "Tools already do", "Search company files, summarize them, show sources and follow file permissions.", "blue", "white", 9.3)
    card(c, 347, 188, 265, 164, "Workflow to test", "Owner opts in. Set a response time. Keep the requester's file access. Ask a human when needed.", "green", "white", 9.3)
    card(c, 642, 188, 265, 164, "Open question", "Do teams need this extra handoff, or can existing tools do the job?", "coral", "peach", 9.3)
    ptext(c,"No public review proves this exact workflow is unique.",66,395,820,20,11,"forest",bold=True,align=1)
    footer_source(c,"Sources and limitations: see the companion PowerPoint speaker notes.")


def slide13(c):
    base(c, 13, "12 / Example economics", "Time value is not the same as cash saved", "Compare estimated recovered work time with costs in AED (UAE dirhams).")
    chart_left, chart_top, chart_h, base_y = 72, 200, 260, 460
    line(c,chart_left,base_y,570,base_y,"muted",.7)
    vals=[125,700,1611];labels=["LOW","BASE","HIGH"];fills=["blue","green","mint"]
    for i,v in enumerate(vals):
        x=108+i*145;h=v/1800*chart_h
        rect(c,x,base_y-h,78,h,fills[i],8)
        ptext(c,f"AED {v:,}k",x-15,base_y-h-23,108,9.6,"forest",bold=True,align=1)
        ptext(c,labels[i],x-3,base_y+9,84,8,"muted",bold=True,align=1)
    cost_top=base_y-740/1800*chart_h
    line(c,65,cost_top,572,cost_top,"coral",1.8,[5,3])
    ptext(c,"Example annual operating cost: AED 740k",335,cost_top-17,230,12,7.7,"coral",bold=True,align=2)
    rect(c,610,179,296,282,"white",12,"line")
    ptext(c,"BASE EXAMPLE · VALUE OF TIME",635,203,240,14,7.8,"green",bold=True)
    ptext(c,"AED 700k",635,237,240,42,29,"forest",bold=True)
    ptext(c,"8,400 answers people accept\n× 20 minutes of search saved\n× AED 250 per work hour",635,301,220,73,10,"muted",15)
    ptext(c,"Time value is AED 40k below example cost",635,399,220,28,8.3,"coral",bold=True)
    ptext(c,"Assumptions only. No work time or financial benefit has been measured.",66,475,820,16,9,"muted",bold=True,align=1)
    footer_source(c)


def slide14(c):
    base(c,14,"13 / Next steps","A path from demo to a safe pilot","Review security and file access. Then connect Microsoft. Then measure value.")
    phases=[("NOW","Local demo","Fictional people and files\nRules and file-access checks\nAnswer or human handoff","Working","green"),
            ("STEP 1","Safety review","Review file labels\nCheck owner permission\nAgree on data handling","Needs review","blue"),
            ("STEP 2","Connect Microsoft","Work sign-in\nRequester file access\nTeams app","Needs tenant setup","gold"),
            ("STEP 3","Small pilot","One opt-in team\nLow-risk files\nMeasure time and trust","6–10 weeks","coral")]
    for i,(tag,h,b,status,accent) in enumerate(phases):
        x=48+i*220;rect(c,x,184,198,240,"white",12,"line")
        pill(c,tag,x+17,201,72,"pale" if i==0 else "lavender","green" if i==0 else "blue")
        ptext(c,h,x+17,244,164,25,14,"forest",bold=True)
        ptext(c,b,x+17,284,164,85,9.5,"muted",14)
        ptext(c,status,x+17,389,164,18,8.3,accent,bold=True)
        if i<3: line(c,x+200,303,x+216,303)
    ptext(c,"No live Microsoft connection has been tested. No language model is used. This is not security-certified.",64,453,830,28,9.2,"coral",bold=True,align=1)
    footer_source(c)


def slide15(c):
    base(c,15,None,None,dark=True)
    pill(c,"PILOT PROPOSAL",58,52,125,"forest","mint")
    ptext(c,"Test the workflow\nwith one willing team.",58,114,670,85,32,"white",37,True)
    items=[("01","One willing team","Use existing, low-risk files"),("02","6–10 weeks","Review security and connect Microsoft"),("03","Safety first","Stop if anyone sees a file they should not"),("04","Measure value","Search time saved, accepted answers, cost")]
    for i,(n,h,b) in enumerate(items):
        top=244+i*41
        ptext(c,n,62,top,37,17,10,"mint",bold=True)
        ptext(c,h,110,top,210,18,11.4,"white",bold=True)
        ptext(c,b,326,top,330,18,8.8,"muted")
    rect(c,675,264,232,126,"forest",12)
    ptext(c,"The ask",700,285,180,18,10,"mint",bold=True)
    ptext(c,"Sponsor a security review, Microsoft setup and one pilot manager.",700,315,180,55,10.3,"white",14)
    ptext(c,"Human API · Show sources, limits and a human path when the answer is not there.",60,466,600,17,8.8,"mint")


BUILDERS=[slide1,slide2,slide3,slide4,slide5,slide6,slide7,slide8,slide9,slide10,slide11,slide12,slide13,slide14,slide15]


def main():
    c=canvas.Canvas(str(OUT), pagesize=(W,H), pageCompression=1)
    c.setTitle("Human API Pitch Deck")
    c.setAuthor("Human API · Eureka Innovation Hackathon")
    for i,fn in enumerate(BUILDERS,1):
        fn(c)
        c.showPage()
    c.save()
    print(f"Wrote matching 16:9 PDF with {len(BUILDERS)} slides: {OUT}")


if __name__=="__main__": main()
