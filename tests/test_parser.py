from pubmed_paper_fetcher.fetcher import parse_articles

SAMPLE_XML = """
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation><PMID>123</PMID></MedlineCitation>
    <Article>
      <ArticleTitle>Sample</ArticleTitle>
      <ArticleDate><Year>2024</Year><Month>05</Month><Day>01</Day></ArticleDate>
      <AuthorList>
        <Author>
          <LastName>Doe</LastName><ForeName>Jane</ForeName>
          <AffiliationInfo>
            <Affiliation>Acme Biotech Inc., Boston</Affiliation>
          </AffiliationInfo>
        </Author>
      </AuthorList>
    </Article>
  </PubmedArticle>
</PubmedArticleSet>
"""

def test_company_author_detected():
    rows = parse_articles(SAMPLE_XML)
    assert len(rows) == 1
    assert rows[0]["Non-academic Author(s)"] == "Jane Doe"
