# Human API pitch deck

The editable presentation is `HumanAPI_Pitch_Deck.pptx` in the repository's `deliverables/` directory. The PDF uses the same 15-slide content and visual system, rendered directly from the source deck layout for consistent page sizing.

The separate [Human API Business Review](../deliverables/HumanAPI_Business_Review.pptx) uses the unchanged retained template at `templates/Business_Review_Reference.pptx`. It summarizes current prototype evidence, illustrative economics, open decisions and a proposed pilot; it is not a quarterly operating report based on live employee or customer results. Rebuild it with `python3 scripts/build_business_review.py`.

The slide text is written for a general audience. Presenter notes hold the technical detail and source links. Use `../docs/READER_GUIDE.md` for the example, glossary and boundaries between the working demo and future AI or Microsoft integrations.

## Rebuild

Requires Node.js and npm.

```bash
npm ci
npm run build
cd ..
.venv/bin/python scripts/build_pitch_pdf.py
```

The source is `generate_deck.js`. Each slide includes speaker notes with narration, demo cues, and source links where claims need attribution.
