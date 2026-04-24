---
{
  "id": "m1-kb-ag-001",
  "title": "CLI Commands & Tools",
  "author": "m1",
  "confidence": 0.85,
  "tags": [
    "knowledge-extraction",
    "session-analysis",
    "group_ag"
  ],
  "status": "active",
  "topic_id": "m1-kb-ag",
  "label": "good",
  "label_note": "\n- firecrawl_search(query: \"<sub-question keywords>\", limit: 8)\n- **With exa:**\n- web_search_exa(query: \"<sub-question keywords>\", numResults: 8) web_search_advanced_exa(query: \"<keywords>\", numResults: 5, startPublishedDate: \"2025-01-01\")\n- **Search strategy:** - Use 2-3 different keyword variations per sub-question - Mix general and news-focused queries - Aim for 15-30 unique sources total - Prioritize: academic, official, reputable new\n- firecrawl_scrape(url: \"<url>\")\n- crawling_exa(url: \"<ur",
  "applies_when": [],
  "do_not_apply_when": []
}
---

# CLI Commands & Tools

> author: m1 · confidence: 0.85


- firecrawl_search(query: "<sub-question keywords>", limit: 8)
- **With exa:**
- web_search_exa(query: "<sub-question keywords>", numResults: 8) web_search_advanced_exa(query: "<keywords>", numResults: 5, startPublishedDate: "2025-01-01")
- **Search strategy:** - Use 2-3 different keyword variations per sub-question - Mix general and news-focused queries - Aim for 15-30 unique sources total - Prioritize: academic, official, reputable new
- firecrawl_scrape(url: "<url>")
- crawling_exa(url: "<ur
