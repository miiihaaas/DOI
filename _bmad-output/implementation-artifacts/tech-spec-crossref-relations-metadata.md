---
title: 'Crossref Relations metadata podrška'
slug: 'crossref-relations-metadata'
created: '2026-03-20'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Django 5.2+', 'Python 3.13', 'PostgreSQL 16+', 'Jinja2', 'HTMX 2.0.8', 'Alpine.js 3.15.3', 'Bootstrap 5.3+', 'lxml', 'pytest-django', 'Factory Boy']
files_to_modify:
  - 'doi_portal/doi_portal/articles/models.py'
  - 'doi_portal/doi_portal/articles/views.py'
  - 'doi_portal/doi_portal/articles/forms.py'
  - 'doi_portal/doi_portal/articles/urls.py'
  - 'doi_portal/doi_portal/articles/apps.py'
  - 'doi_portal/doi_portal/crossref/services.py'
  - 'doi_portal/doi_portal/crossref/templates/crossref/journal_article.xml.j2'
  - 'doi_portal/doi_portal/crossref/templates/crossref/conference_paper.xml.j2'
  - 'doi_portal/doi_portal/crossref/templates/crossref/book_chapter.xml.j2'
  - 'doi_portal/doi_portal/crossref/templates/crossref/sa_component.xml.j2'
  - 'doi_portal/doi_portal/templates/articles/article_form.html'
  - 'NEW: doi_portal/doi_portal/templates/articles/partials/_relation_list.html'
  - 'NEW: doi_portal/doi_portal/templates/articles/partials/_relation_form.html'
  - 'NEW: doi_portal/doi_portal/articles/tests/test_relations.py'
  - 'NEW: doi_portal/doi_portal/crossref/tests/test_relations_xml.py'
code_patterns:
  - 'ArticleFunding pattern: FK to Article, order field, no SoftDelete, plain models.Model'
  - 'HTMX FBV pattern: funding_add/delete/reorder/form_view with _check_article_permission'
  - 'Form pattern: ModelForm with Bootstrap widget attrs, no clean methods, order excluded'
  - 'Success returns _list partial, error returns _form partial with HX-Retarget + HX-Reswap'
  - 'Jinja2 autoescape enabled for .xml.j2 — no | xml_escape on element text'
  - 'PublisherScopedMixin from doi_portal.publishers.mixins'
  - 'has_publisher_access from doi_portal.core.permissions'
test_patterns:
  - 'pytest-django with @pytest.mark.django_db'
  - 'Factory Boy: ArticleFactory, AuthorFactory, IssueFactory, JournalFactory'
  - 'PreValidation tests: TestPreValidationServiceArticle class pattern'
  - 'Service instantiated inside test, validate_issue called, assert on result.errors/warnings'
---

# Tech-Spec: Crossref Relations metadata podrška

**Created:** 2026-03-20

## Overview

### Problem Statement

Aplikacija ne podržava Crossref relations metadata — ne može se definisati veza između dva DOI-ja (erratum, preprint, prevod, supplement, itd.). Crossref podržava ovo kroz `<rel:program name="relations">` element sa `<rel:intra_work_relation>` i `<rel:inter_work_relation>` pod-elementima unutar `journal_article`, `conference_paper`, `content_item` (book chapter), i `component` elemenata.

### Solution

Novi `ArticleRelation` model sa FK ka Article, proširenje sva tri XML template-a + `sa_component.xml.j2` da uključe `<rel:program>` element, proširenje `CrossrefService._build_context()` i `PreValidationService`, HTMX inline UI za upravljanje relacijama na Article form stranici (isti pattern kao Funding).

### Scope

**In Scope:**
- `ArticleRelation` model (FK ka Article, relation_scope, relationship_type, identifier_type, target_identifier, description, order)
- UI za CRUD relacija na Article form stranici (HTMX inline, kao Funding: add/delete/reorder — bez edit)
- XML rendering u sva 3 postojeća template-a + sa_component.xml.j2 (ako postoji pri implementaciji)
- `xmlns:rel="http://www.crossref.org/relations.xsd"` namespace na `<doi_batch>` root
- PreValidationService proširenje (warnings za DOI format, intra_work + non-DOI identifier)
- `_build_context()` proširenje za relations data
- Podrška za sve Crossref relationship tipove (intra_work + inter_work)
- Podrška za sve identifier tipove (doi, issn, isbn, uri, pmid, pmcid, arxiv, other)

**Out of Scope:**
- Auto-detekcija inverzne relacije (ako A isPreprintOf B, ne dodaje automatski hasPreprint na B)
- Relations za Issue/Publication DOI-jeve (samo Article za sada)
- ComponentRelation model (budući rad — kada Component bude trebao, dobije sopstveni model istim pattern-om)

## Context for Development

### Codebase Patterns

- **ArticleFunding pattern** (closest analog): FK ka Article, `order` PositiveIntegerField, plain `models.Model` (ne SoftDeleteMixin), `Meta: ordering = ["order"]`. CRUD: add/delete/reorder/form_view — NEMA edit/update.
- **HTMX FBV pattern**: `@login_required @require_POST`, `_check_article_permission(request.user, article)`, uspeh → return `_list.html` partial, greška → return `_form.html` sa `HX-Retarget` + `HX-Reswap` headerima.
- **Form pattern**: `ModelForm` sa Bootstrap `form-control`/`form-select` widget attrs, srpske labele sa `_()`, nema `clean()` metoda, `order` polje isključeno iz forme.
- **Reorder pattern**: POST sa JSON body `{"order": [pk1, pk2, ...]}`, `for idx, pk in enumerate(order_list)` (0-indexed, kao `funding_reorder`). Napomena: `author_reorder` koristi `enumerate(order_list, start=1)` (1-indexed) — za relations koristiti 0-indexed kao funding.
- **_build_context() pattern**: Fundings se uključuju kao lista dict-ova: `article.fundings.order_by("order")` → `[{"funder_name": ..., "funder_doi": ..., "award_number": ...}]`. Prefetch u `_build_context()`: `.prefetch_related("authors__affiliations", "fundings")` (traži `prefetch_related` string u queriju unutar `_build_context`).
- **XML template autoescape**: Jinja2 Environment ima autoescape uključen za `.xml.j2` — NE koristiti `| xml_escape` na element text. Koristiti `Markup()` za inline XML vrednosti.
- **Namespace deklaracije**: Sve tri template imaju identičan `<doi_batch>` root sa xmlns, xmlns:xsi, xmlns:jats, xmlns:ai, xmlns:fr. Treba dodati `xmlns:rel`.
- **Inline sekcije žive u `article_form.html`** (UpdateView), NE u `article_detail.html` (readonly).
- **Permission check**: `_check_article_permission(user, article)` — traversal `article.issue.publication.publisher`.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `doi_portal/doi_portal/articles/models.py` | ArticleFunding model — pattern za ArticleRelation |
| `doi_portal/doi_portal/articles/views.py` | `funding_add`, `funding_delete`, `funding_reorder`, `funding_form_view` — HTMX pattern (traži "def funding_add" u fajlu) |
| `doi_portal/doi_portal/articles/forms.py` | `ArticleFundingForm` — form pattern (traži "class ArticleFundingForm") |
| `doi_portal/doi_portal/articles/urls.py` | Funding URL patterns (traži "funding" u fajlu) — URL pattern za repliciranje |
| `doi_portal/doi_portal/crossref/services.py` | `_build_context()` — fundings inclusion (traži "fundings" u metodi), prefetch (traži `prefetch_related`). `PreValidationService._validate_article()` — insertion point za relations validation. `validate_issue()` — treba dodati prefetch za relations |
| `doi_portal/doi_portal/crossref/templates/crossref/journal_article.xml.j2` | Element order: ai:program → fr:program → **rel:program** → doi_data. Insert posle poslednjeg `{% endif %}` program bloka (fr:program), pre `<doi_data>` |
| `doi_portal/doi_portal/crossref/templates/crossref/conference_paper.xml.j2` | Element order: fr:program → ai:program → **rel:program** → doi_data. **PAŽNJA**: Redosled fr/ai je OBRNUT u odnosu na journal! Insert posle poslednjeg `{% endif %}` program bloka (ai:program), pre `<doi_data>` |
| `doi_portal/doi_portal/crossref/templates/crossref/book_chapter.xml.j2` | Element order: ai:program → fr:program → **rel:program** → doi_data (isto kao journal). Insert posle poslednjeg `{% endif %}` program bloka (fr:program), pre `<doi_data>` |
| `doi_portal/doi_portal/templates/articles/article_form.html` | Dodati Relations sekciju posle Funding sekcije |
| `doi_portal/doi_portal/crossref/tests/test_validation.py` | Test pattern: `TestPreValidationServiceArticle` klasa |
| `doi_portal/doi_portal/articles/tests/factories.py` | Factory pattern za novi ArticleRelationFactory |
| `docs/project-context.md` | Projekat konvencije i pravila |

### Technical Decisions

- **FK ka Article** (ne GenericForeignKey) — jednostavniji queriji, `select_related` podrška, ContentType se u projektu koristi samo za auditlog
- **Namespace**: `xmlns:rel="http://www.crossref.org/relations.xsd"` (potvrđeno iz XSD targetNamespace)
- **Element pozicija** u XSD sekvenci: `rel:program` ide POSLE poslednjeg od `fr:program`/`ai:program` blokova a PRE `doi_data`. **PAŽNJA**: Redosled fr/ai se razlikuje između template-ova — u `journal_article` i `book_chapter` je ai→fr, u `conference_paper` je fr→ai. Uvek insertovati posle POSLEDNJEG program `{% endif %}` bloka, neposredno pre `<doi_data>`.
- **`<rel:program name="relations">`** — `name` atribut je fixed string "relations" po XSD-u
- **Add/delete/reorder pattern** (kao Funding, bez edit) — relacija ima malo polja, lakše obrisati i ponovo dodati
- **relation_scope se automatski izvodi** iz relationship_type u modelu — `save()` metoda setuje `scope` na osnovu `relationship_type`. UI prikazuje relationship_type grupisan po scope-u u `<optgroup>` dropdown-u.
- **Autoescape** — sav text content u XML template-u se automatski escapuje. Ne treba `| xml_escape`.
- **`<rel:description>`** element je opcioni — renderuje se samo ako `description` polje nije prazno
- **sa_component.xml.j2** — `rel:program` se dodaje unutar `<component>` elementa, posle `<format>` a pre `<doi_data>`

## Implementation Plan

### Tasks

#### Faza 1: Model i migracija

- [ ] Task 1: Dodati ArticleRelation model
  - File: `doi_portal/doi_portal/articles/models.py` (MODIFY)
  - Action: Dodati na kraj fajla (posle ArticleFunding) dve enum klase i model:
    ```python
    class RelationScope(models.TextChoices):
        INTRA_WORK = "intra_work", _("Intra-work (isti rad)")
        INTER_WORK = "inter_work", _("Inter-work (različiti radovi)")

    class IdentifierType(models.TextChoices):
        DOI = "doi", "DOI"
        ISSN = "issn", "ISSN"
        ISBN = "isbn", "ISBN"
        URI = "uri", "URI"
        PMID = "pmid", "PMID"
        PMCID = "pmcid", "PMCID"
        ARXIV = "arxiv", "arXiv"
        OTHER = "other", _("Ostalo")

    INTRA_WORK_TYPES = [
        ("isPreprintOf", "isPreprintOf"),
        ("hasPreprint", "hasPreprint"),
        ("isManuscriptOf", "isManuscriptOf"),
        ("hasManuscript", "hasManuscript"),
        ("isExpressionOf", "isExpressionOf"),
        ("hasExpression", "hasExpression"),
        ("isManifestationOf", "isManifestationOf"),
        ("hasManifestation", "hasManifestation"),
        ("isReplacedBy", "isReplacedBy"),
        ("replaces", "replaces"),
        ("isSameAs", "isSameAs"),
        ("isIdenticalTo", "isIdenticalTo"),
        ("isTranslationOf", "isTranslationOf"),
        ("hasTranslation", "hasTranslation"),
        ("isVersionOf", "isVersionOf"),
        ("hasVersion", "hasVersion"),
    ]

    INTER_WORK_TYPES = [
        ("isSupplementTo", "isSupplementTo"),
        ("isSupplementedBy", "isSupplementedBy"),
        ("isContinuedBy", "isContinuedBy"),
        ("continues", "continues"),
        ("isPartOf", "isPartOf"),
        ("hasPart", "hasPart"),
        ("references", "references"),
        ("isReferencedBy", "isReferencedBy"),
        ("isBasedOn", "isBasedOn"),
        ("isBasisFor", "isBasisFor"),
        ("isRequiredBy", "isRequiredBy"),
        ("requires", "requires"),
        ("isCommentOn", "isCommentOn"),
        ("hasComment", "hasComment"),
        ("isReplyTo", "isReplyTo"),
        ("hasReply", "hasReply"),
        ("isReviewOf", "isReviewOf"),
        ("hasReview", "hasReview"),
    ]

    RELATIONSHIP_TYPE_CHOICES = [
        (_("Intra-work (isti rad, različite verzije)"), INTRA_WORK_TYPES),
        (_("Inter-work (različiti radovi)"), INTER_WORK_TYPES),
    ]

    class ArticleRelation(models.Model):
        article = models.ForeignKey(
            Article, on_delete=models.CASCADE, related_name="relations",
            verbose_name=_("Članak"),
        )
        relationship_type = models.CharField(
            max_length=50, choices=RELATIONSHIP_TYPE_CHOICES,
            verbose_name=_("Tip relacije"),
        )
        relation_scope = models.CharField(
            max_length=20, choices=RelationScope.choices,
            verbose_name=_("Opseg relacije"),
            editable=False,
        )
        identifier_type = models.CharField(
            max_length=10, choices=IdentifierType.choices,
            default=IdentifierType.DOI,
            verbose_name=_("Tip identifikatora"),
        )
        target_identifier = models.CharField(
            max_length=500,
            verbose_name=_("Identifikator cilja"),
        )
        description = models.CharField(
            max_length=500, blank=True,
            verbose_name=_("Opis"),
        )
        order = models.PositiveIntegerField(default=0)

        class Meta:
            ordering = ["order"]
            verbose_name = _("Relacija članka")
            verbose_name_plural = _("Relacije članaka")

        def __str__(self):
            return f"{self.relationship_type} → {self.target_identifier}"

        def save(self, *args, **kwargs):
            intra_types = {t[0] for t in INTRA_WORK_TYPES}
            self.relation_scope = (
                RelationScope.INTRA_WORK if self.relationship_type in intra_types
                else RelationScope.INTER_WORK
            )
            super().save(*args, **kwargs)
    ```
  - Notes: `RELATIONSHIP_TYPE_CHOICES` koristi grouped choices za `<optgroup>` u Select widget. `relation_scope` auto-set u `save()`. Nema SoftDeleteMixin (isto kao ArticleFunding).

- [ ] Task 2: Registrovati ArticleRelation u auditlog
  - File: `doi_portal/doi_portal/articles/apps.py` (MODIFY)
  - Action: U `ready()` metodi (koja već registruje Article, Author, Affiliation) dodati `from .models import ArticleRelation` i `auditlog.register(ArticleRelation)`. Napomena: ArticleFunding NIJE registrovan u auditlog — ArticleRelation dodajemo po Article/Author/Affiliation pattern-u, ne po ArticleFunding pattern-u.

- [ ] Task 3: Kreirati migraciju
  - Action: `python manage.py makemigrations articles`

#### Faza 2: Forma

- [ ] Task 4: Kreirati ArticleRelationForm
  - File: `doi_portal/doi_portal/articles/forms.py` (MODIFY)
  - Action: Dodati posle `ArticleFundingForm`. Import `ArticleRelation` iz `.models`:
    ```python
    class ArticleRelationForm(forms.ModelForm):
        class Meta:
            model = ArticleRelation
            fields = ["relationship_type", "identifier_type", "target_identifier", "description"]
            widgets = {
                "relationship_type": forms.Select(attrs={"class": "form-select"}),
                "identifier_type": forms.Select(attrs={"class": "form-select"}),
                "target_identifier": forms.TextInput(attrs={
                    "class": "form-control",
                    "placeholder": "10.5555/target_doi",
                }),
                "description": forms.TextInput(attrs={
                    "class": "form-control",
                    "placeholder": "Opcioni opis relacije",
                }),
            }
            labels = {
                "relationship_type": _("Tip relacije"),
                "identifier_type": _("Tip identifikatora"),
                "target_identifier": _("Identifikator cilja"),
                "description": _("Opis"),
            }
    ```

#### Faza 3: HTMX views i URL-ovi

- [ ] Task 5: Dodati HTMX views za relations
  - File: `doi_portal/doi_portal/articles/views.py` (MODIFY)
  - Action: Dodati import `ArticleRelationForm` iz `.forms` i `ArticleRelation` iz `.models`. Dodati 4 FBV-a posle funding views, identičan pattern:
    - `relation_add(request, article_pk)` — POST, create, return `_relation_list.html` sa context `{"article": article, "relations": article.relations.all()}`. Error path: return `_relation_form.html` sa context `{"article": article, "relation_form": form}` + `HX-Retarget="#relation-form-container"` + `HX-Reswap="innerHTML"`. **Context variable za formu je `relation_form`** (koristi se i u template-u).
    - `relation_delete(request, pk)` — POST, delete, return `_relation_list.html` sa context `{"article": article, "relations": article.relations.all()}`.
    - `relation_reorder(request, article_pk)` — POST, JSON body `{"order": [...]}`, `for idx, pk in enumerate(order_list)` (0-indexed), return `_relation_list.html`.
    - `relation_form_view(request, article_pk)` — GET, return `_relation_form.html` sa context `{"article": article, "relation_form": ArticleRelationForm()}`.
  - Action: U `ArticleUpdateView.get_context_data()` dodati `context["relations"] = self.object.relations.all()`.

- [ ] Task 6: Dodati URL patterns
  - File: `doi_portal/doi_portal/articles/urls.py` (MODIFY)
  - Action: Posle funding patterns dodati:
    ```python
    path("<int:article_pk>/relations/add/", views.relation_add, name="relation-add"),
    path("relations/<int:pk>/delete/", views.relation_delete, name="relation-delete"),
    path("<int:article_pk>/relations/reorder/", views.relation_reorder, name="relation-reorder"),
    path("<int:article_pk>/relations/form/", views.relation_form_view, name="relation-form"),
    ```

#### Faza 4: HTML templates

- [ ] Task 7: Kreirati _relation_form.html
  - File: `doi_portal/doi_portal/templates/articles/partials/_relation_form.html` (NEW)
  - Action: Po `_funding_form.html` pattern-u. Form sa `hx-post="{% url 'articles:relation-add' article_pk=article.pk %}"`, `hx-target="#relation-section-content"`, `hx-swap="innerHTML"`, CSRF token. Polja renderovati iz **`relation_form`** context variable: `{{ relation_form.relationship_type }}` (select+optgroup), `{{ relation_form.identifier_type }}` (select), `{{ relation_form.target_identifier }}` (text), `{{ relation_form.description }}` (text). Submit dugme "Dodaj relaciju", Cancel dugme (uklanja form container).

- [ ] Task 8: Kreirati _relation_list.html
  - File: `doi_portal/doi_portal/templates/articles/partials/_relation_list.html` (NEW)
  - Action: Po `_funding_list.html` pattern-u. Za svaku relaciju: `relationship_type` badge, `→`, `target_identifier` (sa `identifier_type` label-om), opcioni description italic. Delete dugme sa `hx-post`, `hx-confirm`. Empty state "Nema definisanih relacija."

- [ ] Task 9: Dodati Relations sekciju u article_form.html
  - File: `doi_portal/doi_portal/templates/articles/article_form.html` (MODIFY)
  - Action: Posle Funding sekcije dodati card sa `x-data="relationList()"`:
    ```html
    <div class="card shadow-sm mt-4 section-card" x-data="relationList()">
        <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0"><i class="bi bi-diagram-3 me-2"></i>Srodne publikacije</h5>
            <button type="button" class="btn btn-sm btn-outline-primary"
                    hx-get="{% url 'articles:relation-form' article_pk=object.pk %}"
                    hx-target="#relation-form-container"
                    hx-swap="innerHTML">
                <i class="bi bi-plus-lg me-1"></i>Dodaj
            </button>
        </div>
        <div class="card-body">
            <div id="relation-form-container"></div>
            <div id="relation-section-content">
                {% include "articles/partials/_relation_list.html" with relations=relations %}
            </div>
        </div>
    </div>
    ```
    **VAŽNO**: `{% include %}` MORA koristiti `with relations=relations` klauzulu (kao funding: `with fundings=fundings`).

- [ ] Task 9a: Dodati `relationList()` Alpine.js komponentu
  - File: `doi_portal/doi_portal/templates/articles/article_form.html` (MODIFY)
  - Action: U inline `<script>` bloku na dnu template-a (gde su `fundingList()` i slične Alpine komponente), dodati `relationList()` po `fundingList()` pattern-u:
    ```javascript
    function relationList() {
        return {
            init() {
                this.$nextTick(() => {
                    const container = document.getElementById('relation-container');
                    if (container) {
                        new Sortable(container, {
                            handle: '.drag-handle',
                            animation: 150,
                            onEnd: (evt) => {
                                const items = container.querySelectorAll('[data-relation-id]');
                                const order = Array.from(items).map(item => item.dataset.relationId);
                                fetch(`{% url 'articles:relation-reorder' article_pk=object.pk %}`, {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                                    },
                                    body: JSON.stringify({order: order}),
                                });
                            },
                        });
                    }
                });
            },
        };
    }
    ```
  - Notes: Ovo je kopija `fundingList()` pattern-a sa zamenjenim ID-jevima i URL-om. `#relation-container` je ID na root elementu u `_relation_list.html`, `data-relation-id` je data atribut na svakom relation item-u.

#### Faza 5: XML rendering

- [ ] Task 10: Dodati `xmlns:rel` namespace u XML template-ove
  - Files: `journal_article.xml.j2`, `conference_paper.xml.j2`, `book_chapter.xml.j2` (MODIFY all 3)
  - Action: Na `<doi_batch>` root dodati `xmlns:rel="http://www.crossref.org/relations.xsd"` posle `xmlns:fr` linije.
  - Notes: Ako `sa_component.xml.j2` postoji, dodati i tu.

- [ ] Task 11: Dodati rel:program blok u journal_article.xml.j2
  - File: `doi_portal/doi_portal/crossref/templates/crossref/journal_article.xml.j2` (MODIFY)
  - Action: U ovom template-u redosled je: ai:program → fr:program → doi_data. Traži poslednji `{% endif %}` pre `<doi_data>` (to je kraj fr:program bloka). Insertovati POSLE tog `{% endif %}`, PRE `<doi_data>`:
    ```xml
              {% if article.relations %}
              <rel:program name="relations">
                {% for relation in article.relations %}
                <rel:related_item>
                  {% if relation.description %}
                  <rel:description>{{ relation.description }}</rel:description>
                  {% endif %}
                  {% if relation.scope == "intra_work" %}
                  <rel:intra_work_relation relationship-type="{{ relation.relationship_type }}" identifier-type="{{ relation.identifier_type }}">{{ relation.identifier }}</rel:intra_work_relation>
                  {% else %}
                  <rel:inter_work_relation relationship-type="{{ relation.relationship_type }}" identifier-type="{{ relation.identifier_type }}">{{ relation.identifier }}</rel:inter_work_relation>
                  {% endif %}
                </rel:related_item>
                {% endfor %}
              </rel:program>
              {% endif %}
    ```

- [ ] Task 12: Dodati rel:program blok u conference_paper.xml.j2
  - File: `doi_portal/doi_portal/crossref/templates/crossref/conference_paper.xml.j2` (MODIFY)
  - Action: **PAŽNJA — redosled je OBRNUT u odnosu na journal/book**: ovde je fr:program → ai:program → doi_data. Traži poslednji `{% endif %}` pre `<doi_data>` (to je kraj **ai:program** bloka, NE fr:program). Insertovati POSLE tog `{% endif %}`, PRE `<doi_data>` — isti rel:program blok kao u Task 11.

- [ ] Task 13: Dodati rel:program blok u book_chapter.xml.j2
  - File: `doi_portal/doi_portal/crossref/templates/crossref/book_chapter.xml.j2` (MODIFY)
  - Action: Redosled je isti kao journal: ai:program → fr:program → doi_data. Traži poslednji `{% endif %}` pre `<doi_data>` (kraj fr:program bloka). Insertovati POSLE tog `{% endif %}`, PRE `<doi_data>` — isti rel:program blok kao u Task 11.

- [ ] Task 14: Dodati rel:program u sa_component.xml.j2 (conditional)
  - File: `sa_component.xml.j2` (MODIFY, ako postoji)
  - Action: Unutar `<component>`, posle `<format>` pre `<doi_data>`, dodati isti blok ali sa `component.relations` umesto `article.relations`. Dodati `xmlns:rel` na `<doi_batch>`.

#### Faza 6: Service proširenje

- [ ] Task 15: Proširiti _build_context() za relations
  - File: `doi_portal/doi_portal/crossref/services.py` (MODIFY)
  - Action:
    1. Prefetch: dodati `"relations"` u `.prefetch_related("authors__affiliations", "fundings", "relations")`
    2. U article dict dodati:
       ```python
       "relations": [
           {
               "relationship_type": r.relationship_type,
               "identifier_type": r.identifier_type,
               "identifier": r.target_identifier,
               "description": r.description,
               "scope": r.relation_scope,
           }
           for r in article.relations.order_by("order")
       ],
       ```

- [ ] Task 16: Proširiti PreValidationService
  - File: `doi_portal/doi_portal/crossref/services.py` (MODIFY)
  - Action:
    1. U `validate_issue()` metodi, dodati `"relations"` u prefetch na article queriju. Trenutni queryset je `issue.articles.filter(status=..., is_deleted=False)` — proširiti ga sa `.prefetch_related("relations")` da se izbegne N+1 query problem. Napomena: `_build_context()` ima svoj prefetch — oba mesta treba ažurirati.
    2. U `_validate_article()`, posle author validacije, dodati relations validaciju:
       - ERROR: prazan `target_identifier`
       - WARNING: `identifier_type="doi"` ali `target_identifier` ne počinje sa "10."
       - WARNING: `relation_scope="intra_work"` ali `identifier_type != "doi"`
  - Notes: Koristiti `result.add_error()` / `result.add_warning()` sa `fix_url=reverse("articles:update", kwargs={"pk": article.pk})`.

#### Faza 7: Testovi

- [ ] Task 17: Kreirati ArticleRelationFactory
  - File: `doi_portal/doi_portal/articles/tests/factories.py` (MODIFY)
  - Action: Dodati factory sa default `relationship_type="isSupplementTo"`, `identifier_type="doi"`, `target_identifier=Sequence("10.5555/target.{n}")`.

- [ ] Task 18: Kreirati model i view testove
  - File: `doi_portal/doi_portal/articles/tests/test_relations.py` (NEW)
  - Action: Model tests (auto-scope, __str__), form tests (grouped choices), view tests (add/delete/reorder/form, permissions).

- [ ] Task 19: Kreirati XML i validation testove
  - File: `doi_portal/doi_portal/crossref/tests/test_relations_xml.py` (NEW)
  - Action: PreValidation tests (DOI format, intra+non-DOI, empty identifier). XML generation tests (rel:program present/absent, intra/inter elements, description, XSD validation).

### Acceptance Criteria

#### Model
- [ ] AC 1: Given an Article, when creating ArticleRelation with relationship_type="isPreprintOf", then relation_scope is auto-set to "intra_work".
- [ ] AC 2: Given an Article, when creating ArticleRelation with relationship_type="isSupplementTo", then relation_scope is auto-set to "inter_work".
- [ ] AC 3: Given an ArticleRelation, when __str__() is called, then returns "{relationship_type} → {target_identifier}".

#### UI
- [ ] AC 4: Given Article in edit mode, when "Dodaj" clicked in Relations section, then form appears with relationship_type dropdown showing grouped optgroups.
- [ ] AC 5: Given valid relation form, when POSTed via HTMX, then relation created and list refreshed.
- [ ] AC 6: Given relation in list, when delete clicked with confirmation, then removed and list refreshed.
- [ ] AC 7: Given multiple relations, when reordered via drag-drop, then new order persisted.

#### XML generation
- [ ] AC 8: Given Article with 2 relations (intra isPreprintOf DOI + inter isSupplementTo URI), when XML generated, then `<rel:program name="relations">` contains correct `<rel:intra_work_relation>` and `<rel:inter_work_relation>` with correct attributes.
- [ ] AC 9: Given Article with no relations, when XML generated, then NO `<rel:program>` element.
- [ ] AC 10: Given relation with description, when XML generated, then `<rel:description>` present.
- [ ] AC 11: Given relation without description, when XML generated, then NO `<rel:description>`.
- [ ] AC 12: Given XML with relations, when XSD validated, then passes (xsd_valid=True).
- [ ] AC 13: Given all three template types, when XML generated with relations, then rel:program in correct position and `xmlns:rel` declared.

#### Pre-validation
- [ ] AC 14: Given relation with identifier_type="doi" and target_identifier="invalid", then WARNING about DOI format.
- [ ] AC 15: Given intra_work relation with identifier_type="uri", then WARNING about non-DOI.
- [ ] AC 16: Given relation with empty target_identifier, then ERROR.

## Additional Context

### Dependencies

- Nema novih Python dependency-ja
- Zavisi od `articles` app-a (Article model, views, forms, urls, templates)
- Zavisi od `crossref` app-a (CrossrefService, PreValidationService, XML templates)
- Opciono: `sa_component.xml.j2` iz Component spec-a

### Testing Strategy

**Unit testovi:** Model (auto-scope, __str__), Form (grouped choices, required), Views (HTMX add/delete/reorder/form, permissions)

**Integration testovi:** XML+XSD za sva 3 tipa sa relacijama. PreValidation scenariji. Full workflow (create relations → generate XML → validate XSD).

**Manual testing:** Optgroup dropdown, HTMX add/delete, XML preview sa relacijama, XML bez relacija ne sadrži rel:program.

### Notes

- **XSD element ordering** potvrđen: rel:program uvek ide posle poslednjeg od fr/ai:program blokova, neposredno pre doi_data. **PAŽNJA**: redosled fr/ai se razlikuje: journal+book imaju ai→fr, conference ima fr→ai. Uvek tražiti poslednji `{% endif %}` pre `<doi_data>`.
- **`<rel:program name="relations">`** — `name` fixed po XSD-u
- **Grouped choices**: Django Select widget automatski renderuje `<optgroup>` za tuple-of-tuples format
- **Rizik — XSD namespace**: Dodavanje `xmlns:rel` neće uticati na postojeće validacije — testirati rano
- **ArticleFunding vs ArticleRelation auditlog**: ArticleFunding NIJE registrovan u auditlog. ArticleRelation JESTE — prati Article/Author/Affiliation pattern.
- **Alpine.js SortableJS**: `relationList()` komponenta je neophodna za drag-and-drop reorder. Bez nje AC 7 ne prolazi.
- **Context variable naming**: Forma se prosleđuje kao `relation_form` (ne `form`) u svim views i templates. Lista se prosleđuje kao `relations`.
- **Reorder indexing**: 0-indexed (`enumerate(order_list)`) kao funding, NE 1-indexed kao author.
- **N+1 prevencija**: Prefetch `"relations"` treba dodati na DVA mesta: `_build_context()` queriju i `validate_issue()` queriju.
- **Buduće**: ComponentRelation (isti model pattern, FK ka Component), auto-inverzne relacije
- **sa_component XSD**: rel:program ide posle `<format>` pre `<doi_data>` unutar `<component>`
